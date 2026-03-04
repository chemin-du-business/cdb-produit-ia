from __future__ import annotations

import os
from typing import Any, Dict
from urllib.parse import quote_plus

import requests


PINTEREST_API_BASE = "https://api.pinterest.com/v5"


def fetch_pinterest_signal(query: str) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"hits": 0, "image_url": None, "source_url": None}

    token = (os.environ.get("PINTEREST_ACCESS_TOKEN") or "").strip()
    if not token:
        return {
            "hits": 0,
            "image_url": None,
            "source_url": f"https://www.pinterest.com/search/pins/?q={quote_plus(q)}",
        }

    url = f"{PINTEREST_API_BASE}/search/partner/pins"
    params = {"term": q, "limit": 10}

    try:
        r = requests.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=20,
        )
        data = r.json() if r.content else {}
        items = data.get("items") or []
        hits = len(items)

        image_url = None
        source_url = None

        if items:
            first = items[0] or {}
            source_url = first.get("link") or first.get("url") or None

            media = first.get("media") or {}
            images = (media.get("images") or {}) if isinstance(media, dict) else {}

            for key in ["original", "large", "medium", "small"]:
                img = images.get(key) or {}
                u = img.get("url")
                if u:
                    image_url = u
                    break

        return {"hits": hits, "image_url": image_url, "source_url": source_url}

    except Exception:
        return {
            "hits": 0,
            "image_url": None,
            "source_url": f"https://www.pinterest.com/search/pins/?q={quote_plus(q)}",
        }
