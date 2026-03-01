from __future__ import annotations
from typing import Any, Dict, List
import os
from scripts.connectors.apify_client import run_actor_get_items

DEFAULT_TIKTOK_ACTOR = os.environ.get("APIFY_TIKTOK_ACTOR", "clockworks/tiktok-scraper")

def _to_int(x: Any) -> int:
    try:
        return int(x or 0)
    except Exception:
        return 0

def fetch_tiktok_signal(query: str, results_limit: int = 20, proxy_country_code: str = "FR") -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"provider": "apify", "video_count": 0, "views": 0, "likes": 0, "comments": 0, "shares": 0, "top_videos": [], "source_url": None}

    input_payload = {
        "search": [q],
        "resultsPerPage": min(10, max(1, results_limit)),
        "proxyCountryCode": proxy_country_code,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadSubtitles": False,
        "scrapeRelatedVideos": False,
        "excludePinnedPosts": True,
    }

    items = run_actor_get_items(DEFAULT_TIKTOK_ACTOR, input_payload, timeout_sec=240, items_limit=results_limit)

    views = likes = comments = shares = 0
    top_videos: List[Dict[str, Any]] = []

    for it in items:
        v = _to_int(it.get("playCount") or it.get("views") or it.get("viewCount"))
        l = _to_int(it.get("diggCount") or it.get("likes") or it.get("likeCount"))
        c = _to_int(it.get("commentCount") or it.get("comments"))
        s = _to_int(it.get("shareCount") or it.get("shares"))

        views += v
        likes += l
        comments += c
        shares += s

        url = it.get("webVideoUrl") or it.get("videoUrl") or it.get("url")
        if url and len(top_videos) < 5:
            top_videos.append({"url": url, "views": v, "likes": l, "comments": c, "shares": s})

    source_url = f"https://www.tiktok.com/search?q={q.replace(' ', '%20')}"
    return {
        "provider": "apify",
        "video_count": len(items),
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "top_videos": top_videos,
        "source_url": source_url,
    }