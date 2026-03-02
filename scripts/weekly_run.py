#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trending pipeline (weekly_run.py)

Flow:
1) Google Trends -> candidates
2) Basic product filter (before IA)
3) Fetch signals:
   - TikTok via RapidAPI (ScrapTik) /search-posts
   - Pinterest via RapidAPI (Unofficial Pinterest API) relevance pins
4) Score + diversify categories
5) AI gate (OpenAI): keep only "product vendable" + generate analysis fields
6) Download best image (bytes) -> upload to Supabase Storage
7) Insert rows into public.products + public.runs

ENV required:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_BUCKET (default: product-images)
- RAPIDAPI_KEY
- OPENAI_API_KEY (optional if COLD_MODE=true)
- OPENAI_MODEL (default: gpt-4.1-mini)

Optional ENV:
- TRENDS_GEO (default: FR)
- TIKTOK_REGION (default: FR)
- TIKTOK_PUBLISH_TIME (default: 7)   # 7 = this week (recommended)
- TIKTOK_SORT_TYPE (default: 0)      # 0 = relevance (recommended)
- PINTEREST_NUM (default: 20)
- TIKTOK_COUNT (default: 20)
- TRENDING_LIMIT (default: 10)
- MIN_CANDIDATES (default: 40)
- MAX_PER_CATEGORY (default: 3)
- COLD_MODE (default: false)         # if true => skip OpenAI + keep only scored products

Notes:
- This script uses pytrends. In CI, Google can return 0 candidates (or block). We hard-fallback on seeds.
"""

from __future__ import annotations

import os
import re
import json
import time
import math
import uuid
import hashlib
import random
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import httpx

# pytrends can be flaky; keep it isolated
try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None


# ----------------------------
# Config
# ----------------------------

MIN_CANDIDATES = int(os.getenv("MIN_CANDIDATES", "40"))
TRENDING_LIMIT = int(os.getenv("TRENDING_LIMIT", "10"))
MAX_PER_CATEGORY = int(os.getenv("MAX_PER_CATEGORY", "3"))

TRENDS_GEO = os.getenv("TRENDS_GEO", "FR")
TIKTOK_REGION = os.getenv("TIKTOK_REGION", "FR")
TIKTOK_PUBLISH_TIME = str(os.getenv("TIKTOK_PUBLISH_TIME", "7"))  # "7" recommended
TIKTOK_SORT_TYPE = str(os.getenv("TIKTOK_SORT_TYPE", "0"))        # "0" relevance recommended

TIKTOK_COUNT = str(os.getenv("TIKTOK_COUNT", "20"))
PINTEREST_NUM = str(os.getenv("PINTEREST_NUM", "20"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "product-images")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

COLD_MODE = os.getenv("COLD_MODE", "false").lower() in ("1", "true", "yes", "y", "on")

# RapidAPI hosts (do NOT need to be secrets; only keys are secrets)
TIKTOK_RAPIDAPI_HOST = os.getenv("TIKTOK_RAPIDAPI_HOST", "scraptik.p.rapidapi.com")
PINTEREST_RAPIDAPI_HOST = os.getenv("PINTEREST_RAPIDAPI_HOST", "unofficial-pinterest-api.p.rapidapi.com")

# Endpoints based on your screenshots
TIKTOK_ENDPOINT = os.getenv("TIKTOK_ENDPOINT", f"https://{TIKTOK_RAPIDAPI_HOST}/search-posts")
PINTEREST_ENDPOINT = os.getenv("PINTEREST_ENDPOINT", f"https://{PINTEREST_RAPIDAPI_HOST}/pinterest/pins/relevance")

# Hard fallback seeds (broad, “producty”)
BROAD_SEEDS = [
    "accessoire", "outil", "gadget", "maison", "cuisine", "beauté",
    "sport", "fitness", "bébé", "animaux", "voiture", "bureau",
    "rangement", "nettoyage", "lumière", "jardin", "bricolage",
]

# Avoid non-products (sports, politics, persons, news-ish)
NEGATIVE_KEYWORDS = {
    "match", "ligue", "foot", "football", "psg", "real madrid", "nba", "nfl",
    "président", "politique", "élection", "guerre", "ukraine", "israël", "gaza",
    "acteur", "actrice", "youtubeur", "influenceur", "maire", "ministre",
    "météo", "bourse", "bitcoin", "crypto", "cours", "score", "résultat",
}

# Quick category mapping (used before IA / and for diversity fallback)
CATEGORY_RULES: List[Tuple[str, str]] = [
    ("beauté", "beauté"),
    ("skincare", "beauté"),
    ("maquillage", "beauté"),
    ("cuisine", "maison"),
    ("rangement", "maison"),
    ("nettoyage", "maison"),
    ("fitness", "sport"),
    ("sport", "sport"),
    ("bébé", "bébé"),
    ("chien", "animaux"),
    ("chat", "animaux"),
    ("voiture", "voiture"),
    ("bureau", "bureau"),
    ("gadg", "gadgets"),
    ("gadget", "gadgets"),
]


# ----------------------------
# Helpers
# ----------------------------

def utc_today_date() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[’'`]", "", text)
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ", "-")
    text = re.sub(r"-{2,}", "-", text)
    if not text:
        text = "item"
    return text[:80]

def stable_slug(title: str) -> str:
    base = slugify(title)
    h = hashlib.sha1(title.encode("utf-8")).hexdigest()[:6]
    return f"{base}-{h}"

def clamp_int(x: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(x))))

def safe_get(d: Any, path: List[Any], default=None):
    cur = d
    try:
        for p in path:
            if isinstance(cur, dict):
                cur = cur.get(p)
            elif isinstance(cur, list) and isinstance(p, int):
                cur = cur[p]
            else:
                return default
        return cur if cur is not None else default
    except Exception:
        return default

def guess_category(q: str) -> str:
    t = q.lower()
    for k, cat in CATEGORY_RULES:
        if k in t:
            return cat
    return "autre"

def is_productish_query(q: str) -> bool:
    t = q.lower().strip()
    if len(t) < 3:
        return False
    if any(bad in t for bad in NEGATIVE_KEYWORDS):
        return False
    # Reject mostly numeric or very short
    if re.fullmatch(r"[0-9\s\-]+", t or ""):
        return False
    # Keep queries that look like items
    return True


# ----------------------------
# Google Trends (best effort)
# ----------------------------

def fetch_google_trends_candidates(geo: str, min_candidates: int) -> List[Dict[str, Any]]:
    """
    Returns list of dicts: { "query": str, "trend_score": float }
    """
    if TrendReq is None:
        return []

    try:
        pytrends = TrendReq(hl="fr-FR", tz=0, retries=1, backoff_factor=0.3, timeout=(5, 15))
    except Exception:
        return []

    candidates: List[Dict[str, Any]] = []

    # 1) trending searches
    try:
        df = pytrends.trending_searches(pn=geo)
        # df[0] is the query list
        raw_terms = [str(x) for x in df[0].tolist() if x]
        for term in raw_terms:
            if is_productish_query(term):
                candidates.append({"query": term, "trend_score": 70.0})
    except Exception:
        pass

    # 2) supplement via suggestions from broad seeds (soft fallback)
    # (This may still get blocked; we keep it best-effort)
    if len(candidates) < min_candidates:
        for seed in BROAD_SEEDS:
            if len(candidates) >= min_candidates:
                break
            try:
                sugg = pytrends.suggestions(seed) or []
                for s in sugg[:10]:
                    q = (s.get("title") or "").strip()
                    if q and is_productish_query(q):
                        candidates.append({"query": q, "trend_score": 55.0})
                        if len(candidates) >= min_candidates:
                            break
            except Exception:
                continue

    # de-dupe by query
    seen = set()
    out = []
    for c in candidates:
        k = c["query"].lower().strip()
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


def hard_fallback_candidates() -> List[Dict[str, Any]]:
    """
    Always returns something producty even if Google gives 0.
    """
    suffixes = ["produit", "accessoire", "outil", "gadget", "kit"]
    combos = []
    for s in BROAD_SEEDS:
        for suf in suffixes:
            combos.append(f"{s} {suf}")

    # de-dupe + limit
    seen = set()
    out: List[Dict[str, Any]] = []
    for q in combos:
        k = q.lower().strip()
        if k in seen:
            continue
        seen.add(k)
        out.append({"query": q, "trend_score": 45.0})
        if len(out) >= 60:
            break
    random.shuffle(out)
    return out


# ----------------------------
# RapidAPI - TikTok (ScrapTik)
# ----------------------------

def fetch_tiktok_signal(keyword: str) -> Dict[str, Any]:
    """
    Calls RapidAPI Scraptik search-posts endpoint.
    Returns normalized dict: {count, views_sum, likes_sum, max_views, items:[...]}
    """
    if not RAPIDAPI_KEY:
        return {"ok": False, "error": "RAPIDAPI_KEY missing", "count": 0, "views_sum": 0, "likes_sum": 0, "max_views": 0, "items": []}

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": TIKTOK_RAPIDAPI_HOST,
    }
    params = {
        "keyword": keyword,
        "count": TIKTOK_COUNT,
        "offset": "0",
        "use_filters": "0",
        "publish_time": TIKTOK_PUBLISH_TIME,  # 7=this week recommended
        "sort_type": TIKTOK_SORT_TYPE,        # 0=relevance recommended
        "region": TIKTOK_REGION,
    }

    try:
        with httpx.Client(timeout=25) as client:
            r = client.get(TIKTOK_ENDPOINT, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "count": 0, "views_sum": 0, "likes_sum": 0, "max_views": 0, "items": []}

    # The response structure varies; we try multiple paths
    items = (
        safe_get(data, ["data"], []) or
        safe_get(data, ["data", "items"], []) or
        safe_get(data, ["items"], []) or
        []
    )
    if not isinstance(items, list):
        items = []

    views_sum = 0
    likes_sum = 0
    max_views = 0

    norm_items = []
    for it in items:
        # Try multiple stat keys
        play = (
            safe_get(it, ["play_count"], 0) or
            safe_get(it, ["statistics", "playCount"], 0) or
            safe_get(it, ["stats", "playCount"], 0) or
            safe_get(it, ["playCount"], 0) or
            0
        )
        digg = (
            safe_get(it, ["digg_count"], 0) or
            safe_get(it, ["statistics", "diggCount"], 0) or
            safe_get(it, ["stats", "diggCount"], 0) or
            safe_get(it, ["diggCount"], 0) or
            0
        )

        try:
            play_i = int(play)
        except Exception:
            play_i = 0
        try:
            digg_i = int(digg)
        except Exception:
            digg_i = 0

        views_sum += play_i
        likes_sum += digg_i
        max_views = max(max_views, play_i)

        video_url = safe_get(it, ["share_url"]) or safe_get(it, ["shareUrl"]) or safe_get(it, ["url"])
        cover_url = safe_get(it, ["cover"]) or safe_get(it, ["video", "cover"]) or safe_get(it, ["video", "cover_url"])

        norm_items.append({
            "views": play_i,
            "likes": digg_i,
            "video_url": video_url,
            "cover_url": cover_url,
        })

    return {
        "ok": True,
        "count": len(norm_items),
        "views_sum": views_sum,
        "likes_sum": likes_sum,
        "max_views": max_views,
        "items": norm_items,
        "raw": data,
    }


# ----------------------------
# RapidAPI - Pinterest (Unofficial Pinterest API)
# ----------------------------

def fetch_pinterest_signal(keyword: str) -> Dict[str, Any]:
    """
    Calls RapidAPI Unofficial Pinterest API:
      GET /pinterest/pins/relevance?keyword=...&num=...
    Returns: {count, saves_sum, max_saves, image_url, source_url, items:[...]}
    """
    if not RAPIDAPI_KEY:
        return {"ok": False, "error": "RAPIDAPI_KEY missing", "count": 0, "saves_sum": 0, "max_saves": 0, "items": []}

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": PINTEREST_RAPIDAPI_HOST,
    }
    params = {"keyword": keyword, "num": PINTEREST_NUM}

    try:
        with httpx.Client(timeout=25) as client:
            r = client.get(PINTEREST_ENDPOINT, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "count": 0, "saves_sum": 0, "max_saves": 0, "items": []}

    # Many APIs return { status, data: [...] }
    items = safe_get(data, ["data"], []) or safe_get(data, ["items"], []) or []
    if not isinstance(items, list):
        items = []

    saves_sum = 0
    max_saves = 0
    best_image = None
    best_source = None

    norm_items = []
    for it in items:
        # Common fields: save_count / repin_count / saves / repins etc.
        saves = (
            safe_get(it, ["save_count"], 0) or
            safe_get(it, ["repin_count"], 0) or
            safe_get(it, ["saves"], 0) or
            safe_get(it, ["repins"], 0) or
            0
        )
        try:
            saves_i = int(saves)
        except Exception:
            saves_i = 0
        saves_sum += saves_i
        max_saves = max(max_saves, saves_i)

        # image candidates
        img = (
            safe_get(it, ["images", "orig", "url"]) or
            safe_get(it, ["images", "original", "url"]) or
            safe_get(it, ["image_large_url"]) or
            safe_get(it, ["image_medium_url"]) or
            safe_get(it, ["image"], None)
        )
        link = safe_get(it, ["link"]) or safe_get(it, ["url"]) or safe_get(it, ["pin_url"])

        # pick best image (first good)
        if not best_image and isinstance(img, str) and img.startswith("http"):
            best_image = img
            best_source = link if isinstance(link, str) else None

        norm_items.append({
            "saves": saves_i,
            "image_url": img if isinstance(img, str) else None,
            "source_url": link if isinstance(link, str) else None,
        })

    return {
        "ok": True,
        "count": len(norm_items),
        "saves_sum": saves_sum,
        "max_saves": max_saves,
        "best_image_url": best_image,
        "best_source_url": best_source,
        "items": norm_items,
        "raw": data,
    }


# ----------------------------
# Scoring
# ----------------------------

def score_candidate(trend_score: float, tt: Dict[str, Any], pin: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Returns total score 0..100 and breakdown.
    Includes a small penalty if "too viral" but weak breadth.
    """
    # TikTok score (log scale)
    tt_views = float(tt.get("views_sum", 0) or 0)
    tt_likes = float(tt.get("likes_sum", 0) or 0)
    tt_count = float(tt.get("count", 0) or 0)
    tt_max = float(tt.get("max_views", 0) or 0)

    # Pinterest score
    pin_saves_sum = float(pin.get("saves_sum", 0) or 0)
    pin_count = float(pin.get("count", 0) or 0)
    pin_max = float(pin.get("max_saves", 0) or 0)

    # Normalize roughly
    # TikTok views: 0 -> 0, 1M -> ~100
    tiktok_views_norm = min(100.0, 20.0 * math.log10(1.0 + tt_views))  # log10(1M)=6 => ~120 cap
    tiktok_likes_norm = min(100.0, 25.0 * math.log10(1.0 + tt_likes))  # log10(10k)=4 => 100
    tiktok_breadth_norm = min(100.0, (tt_count / 20.0) * 100.0)

    tiktok_score = 0.55 * tiktok_views_norm + 0.25 * tiktok_likes_norm + 0.20 * tiktok_breadth_norm

    # Pinterest: saves + count
    pin_saves_norm = min(100.0, 30.0 * math.log10(1.0 + pin_saves_sum))  # log10(1k)=3 => 90
    pin_breadth_norm = min(100.0, (pin_count / 20.0) * 100.0)
    pin_score = 0.7 * pin_saves_norm + 0.3 * pin_breadth_norm

    # Trend score already 0..100-ish
    trend_norm = float(trend_score)
    trend_norm = max(0.0, min(100.0, trend_norm))

    # Too-viral penalty: 1 video huge but little breadth
    penalty = 0.0
    if tt_max >= 1_500_000 and tt_count <= 5:
        penalty = 8.0
    if tt_max >= 5_000_000 and tt_count <= 8:
        penalty = max(penalty, 12.0)

    total = (0.35 * trend_norm) + (0.40 * tiktok_score) + (0.25 * pin_score) - penalty
    total_i = clamp_int(total, 0, 100)

    breakdown = {
        "trend": clamp_int(trend_norm),
        "tiktok": clamp_int(tiktok_score),
        "pinterest": clamp_int(pin_score),
        "penalty": clamp_int(penalty),
        "tiktok_views_sum": int(tt_views),
        "tiktok_likes_sum": int(tt_likes),
        "tiktok_count": int(tt_count),
        "pinterest_saves_sum": int(pin_saves_sum),
        "pinterest_count": int(pin_count),
    }
    return total_i, breakdown


# ----------------------------
# OpenAI (AI gate + copy)
# ----------------------------

def openai_analyze_product(title: str, category_hint: str, signals: Dict[str, Any], score: int) -> Dict[str, Any]:
    """
    Returns JSON with:
    - is_product (bool)
    - is_sellable (bool)
    - category (text)
    - tags (list[str])
    - summary (short)
    - positioning {promise, target, problem_solved, why_now}
    - hooks [..]
    - objections [{objection, response}]
    - risks [{risk, level}]
    - recommendations {price_range, channels, upsells}
    - confidence {score, reasons[]}
    """
    if COLD_MODE or not OPENAI_API_KEY:
        # minimal fallback
        return {
            "is_product": True,
            "is_sellable": True,
            "category": category_hint,
            "tags": [],
            "summary": "",
            "positioning": {},
            "hooks": [],
            "objections": [],
            "risks": [],
            "recommendations": {},
            "confidence": {"score": 6, "reasons": ["Signals collected", "Basic filter passed"]},
        }

    system = (
        "Tu es un assistant e-commerce. "
        "Tu dois décider si un terme correspond à un PRODUIT vendable (physique ou digital) "
        "et produire un JSON strict. "
        "Refuse tout ce qui est politique, match, news, personnes, événements."
    )

    user = {
        "title": title,
        "category_hint": category_hint,
        "score": score,
        "signals_summary": {
            "tiktok_views_sum": safe_get(signals, ["tiktok", "views_sum"], 0),
            "tiktok_likes_sum": safe_get(signals, ["tiktok", "likes_sum"], 0),
            "pinterest_saves_sum": safe_get(signals, ["pinterest", "saves_sum"], 0),
        },
        "instruction": (
            "Rends UNIQUEMENT un JSON valide, sans markdown, sans texte autour.\n"
            "Schéma JSON attendu:\n"
            "{\n"
            '  "is_product": true/false,\n'
            '  "is_sellable": true/false,\n'
            '  "category": "beauté|maison|sport|bébé|animaux|voiture|bureau|gadgets|autre",\n'
            '  "tags": ["..."],\n'
            '  "summary": "1-2 phrases max",\n'
            '  "positioning": {"promise":"...", "target":"...", "problem_solved":"...", "why_now":"..."},\n'
            '  "hooks": ["...","..."],\n'
            '  "objections": [{"objection":"...", "response":"..."}],\n'
            '  "risks": [{"risk":"...", "level":"low|medium|high"}],\n'
            '  "recommendations": {"price_range":"..-.. EUR", "channels":["TikTok Ads","Meta Ads"], "upsells":["..."]},\n'
            '  "confidence": {"score": 0-10, "reasons":["...","..."]}\n'
            "}\n"
            "Règles:\n"
            "- Si ce n'est pas un produit vendable => is_product=false et is_sellable=false\n"
            "- Sois concis, réaliste, et cohérent avec le titre.\n"
        ),
    }

    payload = {
        "model": OPENAI_MODEL,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        "temperature": 0.3,
    }

    try:
        with httpx.Client(timeout=35) as client:
            r = client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json=payload,
            )
            r.raise_for_status()
            out = r.json()
        text = safe_get(out, ["output", 0, "content", 0, "text"], None)
        if not text:
            # fallback: search any text content
            text = json.dumps(out)
        # parse JSON
        return json.loads(text)
    except Exception:
        # safe fallback
        return {
            "is_product": True,
            "is_sellable": True,
            "category": category_hint,
            "tags": [],
            "summary": "",
            "positioning": {},
            "hooks": [],
            "objections": [],
            "risks": [],
            "recommendations": {},
            "confidence": {"score": 5, "reasons": ["AI unavailable, fallback used"]},
        }


# ----------------------------
# Supabase REST (DB + Storage)
# ----------------------------

def supabase_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }

def upload_image_to_supabase(bucket: str, slug: str, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """
    Upload bytes to Supabase storage. Returns public URL-like path (object path).
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    object_path = f"{utc_today_date().isoformat()}/{slug}.jpg"
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{object_path}"

    headers = supabase_headers()
    headers.update({"Content-Type": content_type})

    with httpx.Client(timeout=45) as client:
        r = client.put(url, headers=headers, content=image_bytes)
        r.raise_for_status()

    return object_path

def upsert_products(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    url = f"{SUPABASE_URL}/rest/v1/products?on_conflict=slug"
    headers = supabase_headers()
    headers.update({
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    })

    with httpx.Client(timeout=45) as client:
        r = client.post(url, headers=headers, json=rows)
        r.raise_for_status()

def upsert_run(run_date: str, status: str, stats: Dict[str, Any], errors: List[Dict[str, Any]]) -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        # If DB not configured, just print.
        print("[WARN] Supabase not configured, skipping runs upsert.")
        return

    url = f"{SUPABASE_URL}/rest/v1/runs?on_conflict=run_date"
    headers = supabase_headers()
    headers.update({
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    })

    payload = [{
        "run_date": run_date,
        "status": status,
        "stats": stats,
        "errors": errors,
    }]

    with httpx.Client(timeout=45) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()


# ----------------------------
# Image download
# ----------------------------

def download_image_bytes(url: str) -> Optional[bytes]:
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return None
    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            if len(r.content) < 5000:
                return None
            return r.content
    except Exception:
        return None


# ----------------------------
# Main
# ----------------------------

def main() -> None:
    started = time.time()
    run_date = utc_today_date().isoformat()

    stats: Dict[str, Any] = {
        "mode": "trending",
        "geo": TRENDS_GEO,
        "limit": TRENDING_LIMIT,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "cold_mode": COLD_MODE,
        "candidates_raw": 0,
        "candidates_after_basic_filter": 0,
        "scored_total": 0,
        "after_ai_gate": 0,
        "final_count": 0,
        "inserted": 0,
        "trends_fallback_used": False,
    }
    errors: List[Dict[str, Any]] = []

    try:
        # 1) Candidates from Trends
        candidates = fetch_google_trends_candidates(geo=TRENDS_GEO, min_candidates=MIN_CANDIDATES)
        stats["candidates_raw"] = len(candidates)

        # HARD FALLBACK if empty
        if not candidates:
            print("[WARN] Google Trends returned 0 candidates. Using hard fallback seeds.")
            candidates = hard_fallback_candidates()
            stats["candidates_raw"] = len(candidates)
            stats["trends_fallback_used"] = True

        # 2) Basic product filter BEFORE IA (important)
        filtered = []
        for c in candidates:
            q = (c.get("query") or "").strip()
            if not q:
                continue
            if is_productish_query(q):
                filtered.append(c)

        # De-dupe again
        seen = set()
        dedup = []
        for c in filtered:
            k = c["query"].lower().strip()
            if k not in seen:
                seen.add(k)
                dedup.append(c)

        stats["candidates_after_basic_filter"] = len(dedup)

        # If still empty, stop as partial (but no crash)
        if not dedup:
            print("[WARN] No candidates after basic filter. Exiting partial.")
            stats["final_count"] = 0
            stats["inserted"] = 0
            stats["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            stats["runtime_sec"] = round(time.time() - started, 3)
            upsert_run(run_date, "partial", stats, errors)
            print(json.dumps({"status": "success", "stats": stats}, ensure_ascii=False))
            return

        # 3) Fetch signals + scoring
        scored: List[Dict[str, Any]] = []
        for c in dedup[: max(80, TRENDING_LIMIT * 8)]:  # widen pool before AI + diversity
            title = c["query"]
            trend_score = float(c.get("trend_score", 50.0))

            tt = fetch_tiktok_signal(title)
            pin = fetch_pinterest_signal(title)

            score, breakdown = score_candidate(trend_score, tt, pin)

            scored.append({
                "title": title,
                "trend_score": trend_score,
                "category_guess": guess_category(title),
                "score": score,
                "score_breakdown": breakdown,
                "signals": {
                    "tiktok": {
                        "ok": tt.get("ok", False),
                        "count": tt.get("count", 0),
                        "views_sum": tt.get("views_sum", 0),
                        "likes_sum": tt.get("likes_sum", 0),
                        "max_views": tt.get("max_views", 0),
                        "items": tt.get("items", [])[:5],
                    },
                    "pinterest": {
                        "ok": pin.get("ok", False),
                        "count": pin.get("count", 0),
                        "saves_sum": pin.get("saves_sum", 0),
                        "max_saves": pin.get("max_saves", 0),
                        "best_image_url": pin.get("best_image_url"),
                        "best_source_url": pin.get("best_source_url"),
                        "items": pin.get("items", [])[:5],
                    },
                },
            })

        stats["scored_total"] = len(scored)

        # Sort by score desc
        scored.sort(key=lambda x: x["score"], reverse=True)

        # 4) Diversify by category (before IA)
        diversified: List[Dict[str, Any]] = []
        per_cat: Dict[str, int] = {}
        for item in scored:
            cat = item["category_guess"]
            if per_cat.get(cat, 0) >= MAX_PER_CATEGORY:
                continue
            diversified.append(item)
            per_cat[cat] = per_cat.get(cat, 0) + 1
            if len(diversified) >= TRENDING_LIMIT * 3:
                break

        # 5) AI gate + content generation
        final_rows: List[Dict[str, Any]] = []
        for item in diversified:
            title = item["title"]
            cat_hint = item["category_guess"]
            score = item["score"]

            analysis = openai_analyze_product(
                title=title,
                category_hint=cat_hint,
                signals=item["signals"],
                score=score,
            )

            is_product = bool(analysis.get("is_product", True))
            is_sellable = bool(analysis.get("is_sellable", True))

            if not (is_product and is_sellable):
                continue

            category = (analysis.get("category") or cat_hint or "autre").strip().lower()
            if category not in {"beauté", "maison", "sport", "bébé", "animaux", "voiture", "bureau", "gadgets", "autre"}:
                category = cat_hint or "autre"

            tags = analysis.get("tags") or []
            if not isinstance(tags, list):
                tags = []

            summary = analysis.get("summary") or ""
            if not isinstance(summary, str):
                summary = ""

            # Pick best image URL (Pinterest first, then TikTok cover)
            pin_best = safe_get(item, ["signals", "pinterest", "best_image_url"])
            tt_cover = None
            tt_items = safe_get(item, ["signals", "tiktok", "items"], []) or []
            for tti in tt_items:
                if isinstance(tti, dict) and isinstance(tti.get("cover_url"), str) and tti["cover_url"].startswith("http"):
                    tt_cover = tti["cover_url"]
                    break

            chosen_image_url = pin_best or tt_cover
            image_source = "pinterest" if pin_best else ("tiktok" if tt_cover else "fallback")

            slug = stable_slug(title)

            image_path = None
            if chosen_image_url:
                img_bytes = download_image_bytes(chosen_image_url)
                if img_bytes:
                    try:
                        image_path = upload_image_to_supabase(SUPABASE_BUCKET, slug, img_bytes)
                    except Exception as e:
                        errors.append({"stage": "image_upload", "title": title, "error": str(e)})

            # source_url: prefer pinterest source url if exists
            source_url = safe_get(item, ["signals", "pinterest", "best_source_url"])
            if not source_url:
                # fallback tiktok video_url
                for tti in tt_items:
                    vu = tti.get("video_url") if isinstance(tti, dict) else None
                    if isinstance(vu, str) and vu.startswith("http"):
                        source_url = vu
                        break

            sources = []
            if safe_get(item, ["signals", "tiktok", "ok"]):
                sources.append("tiktok")
            if safe_get(item, ["signals", "pinterest", "ok"]):
                sources.append("pinterest")
            sources.append("google_trends")

            score_breakdown = item["score_breakdown"]

            # analysis + signals storage
            analysis_payload = analysis
            signals_payload = item["signals"]

            # “UI blocks” structure (from your screenshots)
            # We'll store in analysis JSON; your Next.js can render it.
            ui = {
                "positioning": analysis.get("positioning", {}),
                "hooks": analysis.get("hooks", []),
                "objections": analysis.get("objections", []),
                "risks": analysis.get("risks", []),
                "recommendations": analysis.get("recommendations", {}),
                "confidence": analysis.get("confidence", {}),
            }
            analysis_payload["ui"] = ui

            row = {
                "run_date": run_date,
                "title": title,
                "slug": slug,
                "category": category,
                "tags": tags,
                "sources": sources,
                "score": int(item["score"]),
                "score_breakdown": score_breakdown,
                "summary": summary,
                "signals": signals_payload,
                "analysis": analysis_payload,
                "image_url": image_path,  # IMPORTANT: stored path in bucket (bytes uploaded)
                "image_source": image_source,
                "source_url": source_url,
                "is_hidden": False,
            }

            final_rows.append(row)
            if len(final_rows) >= TRENDING_LIMIT:
                break

        stats["after_ai_gate"] = len(final_rows)
        stats["final_count"] = len(final_rows)

        # 6) Insert in DB
        if final_rows:
            upsert_products(final_rows)
            stats["inserted"] = len(final_rows)

        # 7) Status
        run_status = "success" if stats["inserted"] > 0 else "partial"

        stats["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        stats["runtime_sec"] = round(time.time() - started, 3)

        upsert_run(run_date, run_status, stats, errors)

        print(json.dumps({"status": "success", "stats": stats}, ensure_ascii=False))

    except Exception as e:
        errors.append({"stage": "fatal", "error": str(e)})
        stats["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        stats["runtime_sec"] = round(time.time() - started, 3)

        try:
            upsert_run(run_date, "fail", stats, errors)
        except Exception:
            pass

        print(json.dumps({"status": "fail", "stats": stats, "errors": errors}, ensure_ascii=False))
        raise


if __name__ == "__main__":
    main()