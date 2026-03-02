from __future__ import annotations
from typing import Any, Dict, List
import os
from scripts.connectors.apify_client import run_actor_get_items

DEFAULT_PINTEREST_ACTOR = os.environ.get("APIFY_PINTEREST_ACTOR", "easyapi/pinterest-search-scraper")

def _to_int(x: Any) -> int:
    try:
        return int(x or 0)
    except Exception:
        return 0

def fetch_pinterest_signal(query: str, limit: int = 25) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"provider": "apify", "pin_count": 0, "repin_count": 0, "save_count": 0, "top_pins": [], "image_url": None, "source_url": None}

    items = run_actor_get_items(
        DEFAULT_PINTEREST_ACTOR,
        {"query": q, "filter": "all", "limit": limit},
        timeout_sec=240,
        items_limit=limit
    )

    top_pins: List[Dict[str, Any]] = []
    save_count = 0
    repin_count = 0
    image_url = None

    for it in items:
        img = it.get("imageURL") or it.get("imageUrl") or it.get("image") or it.get("image_url")
        url = it.get("url") or it.get("pinUrl") or it.get("link")
        saves = _to_int(it.get("saveCount") or it.get("saves") or it.get("repins") or it.get("repinCount"))
        repins = _to_int(it.get("repinCount") or it.get("repins"))

        save_count += saves
        repin_count += repins

        if not image_url and isinstance(img, str) and img.startswith("http"):
            image_url = img

        if len(top_pins) < 5:
            top_pins.append({"url": url, "image_url": img, "saves": saves, "repins": repins, "title": it.get("title")})

    source_url = f"https://www.pinterest.com/search/pins/?q={q.replace(' ', '%20')}"
    return {
        "provider": "apify",
        "pin_count": len(items),
        "repin_count": repin_count,
        "save_count": save_count,
        "top_pins": top_pins,
        "image_url": image_url,
        "source_url": source_url,
    }