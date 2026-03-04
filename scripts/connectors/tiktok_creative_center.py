from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urlencode

import requests


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"
)

BASE = "https://ads.tiktok.com/business/creativecenter"

HASHTAGS_URL = f"{BASE}/inspiration/popular/hashtag/pc/en"
TOP_PRODUCTS_URL = f"{BASE}/inspiration/top-products/pc/en"


def _num_from_text(s: str) -> int:
    s = (s or "").strip().upper().replace(",", ".")
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([KM]?)$", s)
    if not m:
        return 0
    v = float(m.group(1))
    suf = m.group(2)
    if suf == "K":
        return int(v * 1_000)
    if suf == "M":
        return int(v * 1_000_000)
    return int(v)


def _fetch_html(url: str, region: str = "FR", timeout: int = 20) -> str:
    qs = urlencode({"region": region, "countryCode": region})
    full = url + ("?" + qs if "?" not in url else "&" + qs)

    r = requests.get(
        full,
        headers={
            "User-Agent": UA,
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
        },
        timeout=timeout,
    )
    return r.text or ""


def _parse_trending_hashtags(html: str, limit: int = 80) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    pat = re.compile(
        r"(\b\d{1,3}\b)\s+#\s*([A-Za-z0-9_]+).*?\s(\d+(?:\.\d+)?[KM]?)\s+Posts",
        re.IGNORECASE,
    )

    for m in pat.finditer(html):
        rank = int(m.group(1))
        tag = m.group(2).strip()
        posts = _num_from_text(m.group(3))

        if not tag:
            continue

        title = tag.replace("_", " ").strip()
        out.append(
            {
                "title": title,
                "sources": ["tiktok_cc"],
                "signals": {
                    "tiktok_cc": {
                        "type": "hashtag",
                        "rank": rank,
                        "posts": posts,
                        "source_url": HASHTAGS_URL,
                    }
                },
            }
        )
        if len(out) >= limit:
            break

    return out


def _parse_top_products(html: str, limit: int = 80) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    candidates = set()

    for m in re.finditer(r'aria-label="([^"]{6,120})"', html):
        txt = m.group(1).strip()
        if txt and len(txt.split()) >= 2:
            candidates.add(txt)

    for m in re.finditer(r'alt="([^"]{6,120})"', html):
        txt = m.group(1).strip()
        if txt and len(txt.split()) >= 2:
            candidates.add(txt)

    BAD = {
        "tiktok for business",
        "view more",
        "see analytics",
        "log in",
        "sign up",
        "search",
        "region",
        "objective",
        "industry",
    }

    cleaned: List[str] = []
    for c in candidates:
        lc = c.lower()
        if any(b in lc for b in BAD):
            continue
        cleaned.append(c)

    cleaned = cleaned[:limit]

    for i, title in enumerate(cleaned, start=1):
        out.append(
            {
                "title": title,
                "sources": ["tiktok_cc"],
                "signals": {
                    "tiktok_cc": {
                        "type": "top_product",
                        "rank": i,
                        "posts": 0,
                        "source_url": TOP_PRODUCTS_URL,
                    }
                },
            }
        )

    return out


def fetch_tiktok_creative_center_candidates(region: str = "FR", limit: int = 120) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    html_prod = _fetch_html(TOP_PRODUCTS_URL, region=region)
    items.extend(_parse_top_products(html_prod, limit=min(80, limit)))

    html_hash = _fetch_html(HASHTAGS_URL, region=region)
    items.extend(_parse_trending_hashtags(html_hash, limit=max(40, limit - len(items))))

    seen = set()
    dedup: List[Dict[str, Any]] = []
    for it in items:
        t = (it.get("title") or "").strip().lower()
        if not t or t in seen:
            continue
        seen.add(t)
        dedup.append(it)

    return dedup[:limit]
