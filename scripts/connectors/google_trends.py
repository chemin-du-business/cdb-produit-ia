from __future__ import annotations

from typing import Any, Dict, List
from pytrends.request import TrendReq
import requests
from urllib.parse import quote_plus


MIN_CANDIDATES = 200

BROAD_SEEDS = [
    "tiktok gadget",
    "viral gadget",
    "amazon finds",
    "beauty gadget",
    "skincare device",
    "kitchen gadget",
    "home gadget",
    "pet gadget",
    "car gadget",
    "cleaning gadget",
    "smart home gadget",
    "portable blender",
    "mini vacuum",
]

BAD_TERMS = [
    "mots fléchés",
    "mots croisés",
    "synonyme",
    "solution",
    "définition",
    "definition",
    "3 lettres",
    "4 lettres",
    "5 lettres",
    "6 lettres",
    "7 lettres",
    "8 lettres",
    "10 lettres",
]

GENERIC_TERMS = [
    "accessoire",
    "produit",
    "objet",
    "article",
    "équipement",
    "equipement",
    "outil",
]

SEO_TERMS = [
    "best ",
    "top ",
    "review",
    "reviews",
    "comparison",
    "compare",
    "vs",
    "guide",
    "how to",
    "comment",
    "avis",
    "test",
    "meilleur",
    "meilleurs",
    "comparatif",
]


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"


def _is_bad_term(term: str) -> bool:
    t = (term or "").strip().lower()
    if not t:
        return True
    if any(x in t for x in BAD_TERMS):
        return True
    if any(x in t for x in SEO_TERMS):
        return True
    if any(x in t for x in GENERIC_TERMS) and len(t.split()) <= 3:
        return True
    if len(t.split()) <= 2:
        return True
    return False


def _autocomplete(seed: str, hl: str = "fr") -> List[str]:
    """
    Fallback ultra-stable (marche sur GitHub Actions) via Google Suggest.
    """
    q = (seed or "").strip()
    if not q:
        return []

    url = f"https://suggestqueries.google.com/complete/search?client=firefox&hl={hl}&q={quote_plus(q)}"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        data = r.json()
        # format: [query, [suggestions...], ...]
        suggs = data[1] if isinstance(data, list) and len(data) > 1 else []
        out = []
        for s in suggs:
            s = str(s).strip()
            if s and not _is_bad_term(s):
                out.append(s)
        return out
    except Exception:
        return []


def _interest_max(pytrends: TrendReq, term: str, geo: str, timeframe: str) -> int:
    try:
        pytrends.build_payload([term], geo=geo, timeframe=timeframe)
        it = pytrends.interest_over_time()
        if it is not None and not it.empty and term in it.columns:
            return int(it[term].max())
    except Exception:
        pass
    return 0


def _related_queries(pytrends: TrendReq, seed: str, geo: str, timeframe: str, cap: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        pytrends.build_payload([seed], geo=geo, timeframe=timeframe)
        related = pytrends.related_queries()
        data = (related.get(seed, {}) or {}) if isinstance(related, dict) else {}

        for kind in ("top", "rising"):
            df = data.get(kind)
            if df is None:
                continue
            for _, row in df.head(cap).iterrows():
                q = str(row.get("query", "")).strip()
                if q and not _is_bad_term(q):
                    out.append({"query": q, "kind": kind})
    except Exception:
        pass

    # dedup
    seen = set()
    dedup = []
    for x in out:
        k = x["query"].lower()
        if k in seen:
            continue
        seen.add(k)
        dedup.append(x)
    return dedup


def fetch_google_trends_candidates(geo: str = "FR", limit_trending: int = 40) -> List[Dict[str, Any]]:
    pytrends = TrendReq(hl="fr-FR", tz=60)
    timeframe = "today 3-m"

    candidates: List[Dict[str, Any]] = []

    # 1) Essai pytrends trending_searches (peut être vide sur GitHub)
    trends: List[str] = []
    try:
        df = pytrends.trending_searches(pn="france")
        trends = [str(x).strip() for x in df[0].tolist() if str(x).strip()][:limit_trending]
    except Exception:
        trends = []

    for trend in trends:
        interest = _interest_max(pytrends, trend, geo, timeframe)
        rel = _related_queries(pytrends, trend, geo, timeframe, cap=25)
        for item in rel:
            candidates.append({
                "title": item["query"],
                "sources": ["google_trends"],
                "signals": {
                    "google_trends": {
                        "seed": trend,
                        "kind": item["kind"],
                        "interest": interest,
                        "timeframe": timeframe,
                    }
                }
            })

    # 2) Seeds via pytrends related_queries
    if len(candidates) < MIN_CANDIDATES:
        for seed in BROAD_SEEDS:
            interest = _interest_max(pytrends, seed, geo, timeframe)
            rel = _related_queries(pytrends, seed, geo, timeframe, cap=25)
            for item in rel:
                candidates.append({
                    "title": item["query"],
                    "sources": ["google_trends"],
                    "signals": {
                        "google_trends": {
                            "seed": seed,
                            "kind": f"fallback_{item['kind']}",
                            "interest": interest,
                            "timeframe": timeframe,
                        }
                    }
                })

    # 3) Fallback ultime ultra stable : Google Autocomplete
    if len(candidates) < MIN_CANDIDATES:
        for seed in BROAD_SEEDS:
            for s in _autocomplete(seed, hl="fr"):
                candidates.append({
                    "title": s,
                    "sources": ["google_trends"],
                    "signals": {
                        "google_trends": {
                            "seed": seed,
                            "kind": "autocomplete",
                            "interest": 0,
                            "timeframe": timeframe,
                        }
                    }
                })

    # dedup global
    seen = set()
    out: List[Dict[str, Any]] = []
    for c in candidates:
        k = (c.get("title") or "").strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(c)

    return out