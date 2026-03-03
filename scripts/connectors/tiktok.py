from __future__ import annotations
from typing import Dict, Any
import requests
from urllib.parse import quote_plus
import re

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"

def fetch_tiktok_signal(query: str) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"hits": 0, "views_estimate": 0, "source_url": None}

    url = f"https://www.tiktok.com/search?q={quote_plus(q)}"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        html = r.text or ""

        # proxy très simple: compter des occurrences de patterns
        # (ceci est V1. On fera mieux avec une source dédiée ensuite)
        hits = len(re.findall(r'"type":"video"', html))
        views_tokens = len(re.findall(r'"playCount"', html))

        views_estimate = views_tokens * 100_000  # proxy
        return {"hits": hits, "views_estimate": views_estimate, "source_url": url}
    except Exception:
        return {"hits": 0, "views_estimate": 0, "source_url": url}