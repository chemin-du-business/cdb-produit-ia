import os
import requests
from typing import Any, Dict, List, Optional


RAPIDAPI_HOST = "scraptik.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"
ENDPOINT = "/search-posts"


def _median(nums: List[int]) -> int:
    nums = sorted(nums)
    if not nums:
        return 0
    mid = len(nums) // 2
    if len(nums) % 2 == 1:
        return nums[mid]
    return (nums[mid - 1] + nums[mid]) // 2


def fetch_tiktok_signal(keyword: str) -> Dict[str, Any]:
    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        return {"ok": False, "error": "Missing RAPIDAPI_KEY"}

    count = os.environ.get("TIKTOK_COUNT", "20")
    region = os.environ.get("TIKTOK_REGION", "FR")

    params = {
        "keyword": keyword,
        "count": str(count),
        "offset": "0",
        "use_filters": "0",
        # publish_time: 7 = this week (recommandé pour Trending)
        "publish_time": os.environ.get("TIKTOK_PUBLISH_TIME", "7"),
        # sort_type: 0 relevance (recommandé)
        "sort_type": os.environ.get("TIKTOK_SORT_TYPE", "0"),
        "region": region,
    }

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }

    try:
        r = requests.get(f"{BASE_URL}{ENDPOINT}", headers=headers, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # The exact response keys can vary; we keep it robust.
    items = data.get("data") or data.get("aweme_list") or data.get("items") or []
    if not isinstance(items, list):
        items = []

    views = []
    likes = []
    for it in items[: int(count)]:
        stats = it.get("statistics") or it.get("stats") or {}
        v = stats.get("play_count") or stats.get("views") or stats.get("viewCount") or 0
        l = stats.get("digg_count") or stats.get("likes") or stats.get("likeCount") or 0
        try:
            views.append(int(v))
        except Exception:
            pass
        try:
            likes.append(int(l))
        except Exception:
            pass

    signal = {
        "posts": int(len(items)),
        "views_median": _median(views),
        "views_top": max(views) if views else 0,
        "likes_median": _median(likes),
        "likes_top": max(likes) if likes else 0,
        "region": region,
        "publish_time": params["publish_time"],
        "sort_type": params["sort_type"],
    }

    return {"ok": True, "signal": signal}