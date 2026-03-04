from __future__ import annotations

import os
import time
from typing import Any, Dict, List
import requests

APIFY_API_BASE = "https://api.apify.com/v2"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"
)

def _apify_token() -> str:
    tok = (os.environ.get("APIFY_TOKEN") or "").strip()
    if not tok:
        raise RuntimeError("APIFY_TOKEN manquant (GitHub Secret).")
    return tok

def _actor_id() -> str:
    return (os.environ.get("APIFY_ACTOR_ID") or "clockworks/tiktok-hashtag-scraper").strip()

def _timeout_seconds() -> int:
    return int(os.environ.get("APIFY_TIMEOUT_SECONDS") or "240")

def _hashtags() -> List[str]:
    raw = (os.environ.get("TIKTOK_HASHTAGS") or "").strip()
    if raw:
        return [x.strip().lstrip("#") for x in raw.split(",") if x.strip()]
    return ["tiktokmademebuyit","amazonfinds","viralproducts","tiktokshopfinds","gadgets"]

def _max_posts_per_hashtag() -> int:
    return int(os.environ.get("TIKTOK_MAX_POSTS_PER_HASHTAG") or "80")

def _limit_total() -> int:
    return int(os.environ.get("TIKTOK_VIDEOS_LIMIT") or "250")

def run_actor_and_get_items(actor_id: str, input_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    token = _apify_token()

    r = requests.post(
        f"{APIFY_API_BASE}/acts/{actor_id}/runs?token={token}",
        json=input_payload,
        timeout=30,
        headers={"User-Agent": UA},
    )
    r.raise_for_status()
    run = (r.json() or {}).get("data") or {}
    run_id = run.get("id")
    if not run_id:
        raise RuntimeError("Apify: run_id introuvable.")

    deadline = time.time() + _timeout_seconds()
    status = "RUNNING"

    while time.time() < deadline:
        rr = requests.get(
            f"{APIFY_API_BASE}/actor-runs/{run_id}?token={token}",
            timeout=30,
            headers={"User-Agent": UA},
        )
        rr.raise_for_status()
        data = (rr.json() or {}).get("data") or {}
        status = data.get("status") or status
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            run = data
            break
        time.sleep(3)

    if status != "SUCCEEDED":
        raise RuntimeError(f"Apify run non réussi: {status}")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise RuntimeError("Apify: defaultDatasetId introuvable.")

    it = requests.get(
        f"{APIFY_API_BASE}/datasets/{dataset_id}/items?token={token}&clean=true",
        timeout=60,
        headers={"User-Agent": UA},
    )
    it.raise_for_status()
    items = it.json()
    return items if isinstance(items, list) else []

def fetch_tiktok_hashtag_videos() -> List[Dict[str, Any]]:
    actor_id = _actor_id()
    hashtags = _hashtags()
    max_posts = _max_posts_per_hashtag()

    input_payload = {
        "hashtags": hashtags,
        "maxPostsPerHashtag": max_posts,
    }

    items = run_actor_and_get_items(actor_id, input_payload)
    return items[:_limit_total()]

def fetch_tiktok_candidates_from_hashtags() -> List[Dict[str, Any]]:
    videos = fetch_tiktok_hashtag_videos()

    out: List[Dict[str, Any]] = []
    seen = set()

    for v in videos:
        if not isinstance(v, dict):
            continue

        caption = str(v.get("text") or "").strip()
        url = str(v.get("webVideoUrl") or "").strip()
        if not caption or not url:
            continue

        if url in seen:
            continue
        seen.add(url)

        likes = int(v.get("diggCount") or 0)
        shares = int(v.get("shareCount") or 0)
        views = int(v.get("playCount") or 0)
        comments = int(v.get("commentCount") or 0)

        author = v.get("authorMeta.name")
        created = v.get("createTimeISO")
        duration = v.get("videoMeta.duration")

        out.append(
            {
                "title": caption,  # caption brute (extraction produit via IA ensuite)
                "sources": ["tiktok_hashtag"],
                "signals": {
                    "tiktok_hashtag": {
                        "video_url": url,
                        "author": author,
                        "created_at": created,
                        "duration_seconds": duration,
                        "views": views,
                        "likes": likes,
                        "comments": comments,
                        "shares": shares,
                    }
                },
            }
        )

    return out
