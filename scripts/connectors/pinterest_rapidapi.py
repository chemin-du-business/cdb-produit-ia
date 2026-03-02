import os
import requests
from typing import Any, Dict, List, Optional


RAPIDAPI_HOST = "unofficial-pinterest-api.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"
ENDPOINT = "/pinterest/pins/relevance"


def _pick_best_image(item: Dict[str, Any]) -> Optional[str]:
    images = item.get("images") or {}
    for size in ["orig", "736x", "474x", "236x", "170x"]:
        obj = images.get(size) or {}
        url = obj.get("url")
        if isinstance(url, str) and url.startswith("http"):
            return url
    return None


def fetch_pinterest_signal(keyword: str, num: int = 30) -> Dict[str, Any]:
    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        return {"ok": False, "error": "Missing RAPIDAPI_KEY"}

    params = {
        "keyword": keyword,
        "num": str(num),
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

    items: List[Dict[str, Any]] = data.get("data", [])
    if not isinstance(items, list):
        items = []

    pins = []
    follower_counts = []

    for it in items:
        img = _pick_best_image(it)
        link = it.get("link")
        title = it.get("grid_title")
        pinner = it.get("pinner") or {}
        fc = pinner.get("follower_count") or 0
        try:
            follower_counts.append(int(fc))
        except Exception:
            pass

        pins.append({
            "id": it.get("id"),
            "pin_url": link,
            "title": title,
            "image_url": img,
            "pinner_followers": fc,
        })

    best_image_url = None
    for p in pins:
        if p.get("image_url"):
            best_image_url = p["image_url"]
            break

    signal = {
        "pins": len(pins),
        "best_image_url": best_image_url,
        "pinner_followers_median": int(sorted(follower_counts)[len(follower_counts)//2]) if follower_counts else 0,
    }

    return {"ok": True, "signal": signal}