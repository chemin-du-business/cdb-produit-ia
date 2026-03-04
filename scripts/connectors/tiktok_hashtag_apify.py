from __future__ import annotations

import os
import time
from typing import Any, Dict, List
from urllib.parse import quote
import requests

APIFY_API_BASE = "https://api.apify.com/v2"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"
)

# -----------------------
# Config helpers
# -----------------------

def _apify_token() -> str:
    tok = (os.environ.get("APIFY_TOKEN") or "").strip()
    if not tok:
        raise RuntimeError("APIFY_TOKEN manquant (GitHub Secret).")
    return tok

def _actor_id() -> str:
    # exemple: "clockworks/tiktok-hashtag-scraper"
    return (os.environ.get("APIFY_ACTOR_ID") or "clockworks/tiktok-hashtag-scraper").strip()

def _timeout_seconds() -> int:
    # Mets 900 dans GitHub Actions si tu download les vidéos
    return int(os.environ.get("APIFY_TIMEOUT_SECONDS") or "900")

def _poll_interval_seconds() -> int:
    return int(os.environ.get("APIFY_POLL_SECONDS") or "4")

def _hashtags() -> List[str]:
    raw = (os.environ.get("TIKTOK_HASHTAGS") or "").strip()
    if raw:
        return [x.strip().lstrip("#") for x in raw.split(",") if x.strip()]
    return ["tiktokmademebuyit", "amazonfinds", "viralproducts", "tiktokshopfinds", "gadgets"]

def _max_posts_per_hashtag() -> int:
    return int(os.environ.get("TIKTOK_MAX_POSTS_PER_HASHTAG") or "40")

def _limit_total() -> int:
    return int(os.environ.get("TIKTOK_VIDEOS_LIMIT") or "200")

# -----------------------
# HTTP helper (petit retry)
# -----------------------

def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    retries = int(os.environ.get("APIFY_HTTP_RETRIES") or "3")
    backoff = float(os.environ.get("APIFY_HTTP_BACKOFF") or "2.0")

    last_exc = None
    for i in range(retries):
        try:
            r = requests.request(method, url, **kwargs)
            # retry sur 502/503/504
            if r.status_code in (502, 503, 504):
                time.sleep(backoff * (i + 1))
                continue
            return r
        except Exception as e:
            last_exc = e
            time.sleep(backoff * (i + 1))
    raise RuntimeError(f"HTTP failed after retries: {url} ({last_exc})")

# -----------------------
# Apify runner
# -----------------------

def run_actor_and_get_items(actor_id: str, input_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    token = _apify_token()
    actor_id_enc = quote(actor_id, safe="")  # encode "/" => "%2F"

    # 1) start run
    start_url = f"{APIFY_API_BASE}/acts/{actor_id_enc}/runs?token={token}"
    r = _request_with_retry(
        "POST",
        start_url,
        json=input_payload,
        timeout=30,
        headers={"User-Agent": UA},
    )

    if r.status_code == 404:
        raise RuntimeError(
            "Apify 404 sur Actor. Vérifie APIFY_ACTOR_ID.\n"
            f"Actor reçu: {actor_id}\n"
            f"URL appelée: {start_url}\n"
            f"Réponse: {r.text[:300]}"
        )

    r.raise_for_status()

    run = (r.json() or {}).get("data") or {}
    run_id = run.get("id")
    if not run_id:
        raise RuntimeError("Apify: run_id introuvable.")

    # 2) poll status
    deadline = time.time() + _timeout_seconds()
    poll = _poll_interval_seconds()

    status = "RUNNING"
    run_data: Dict[str, Any] = {}

    print(f"[Apify] run started: {run_id}")

    while True:
        if time.time() > deadline:
            # run pas fini à temps
            raise RuntimeError(
                f"Apify run pas terminé à temps (status={status}). run_id={run_id}. "
                "Augmente APIFY_TIMEOUT_SECONDS (ex: 900) ou réduis TIKTOK_MAX_POSTS_PER_HASHTAG."
            )

        rr = _request_with_retry(
            "GET",
            f"{APIFY_API_BASE}/actor-runs/{run_id}?token={token}",
            timeout=30,
            headers={"User-Agent": UA},
        )
        rr.raise_for_status()

        run_data = (rr.json() or {}).get("data") or {}
        status = run_data.get("status") or status

        if status == "SUCCEEDED":
            break

        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Apify run terminé en erreur: {status}. run_id={run_id}")

        remaining = int(deadline - time.time())
        print(f"[Apify] status={status} (remaining {remaining}s)")
        time.sleep(poll)

    # 3) get dataset items
    dataset_id = run_data.get("defaultDatasetId")
    if not dataset_id:
        raise RuntimeError("Apify: defaultDatasetId introuvable.")

    items_url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items?token={token}&clean=true"
    it = _request_with_retry(
        "GET",
        items_url,
        timeout=90,
        headers={"User-Agent": UA},
    )
    it.raise_for_status()

    items = it.json()
    return items if isinstance(items, list) else []

# -----------------------
# Public API
# -----------------------

def fetch_tiktok_hashtag_videos() -> List[Dict[str, Any]]:
    actor_id = _actor_id()
    hashtags = _hashtags()
    max_posts = _max_posts_per_hashtag()

    input_payload = {
        "hashtags": hashtags,
        "maxPostsPerHashtag": max_posts,
        "shouldDownloadVideos": True,
    }

    items = run_actor_and_get_items(actor_id, input_payload)
    return items[: _limit_total()]

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

        # IMPORTANT: ces champs peuvent varier selon l’actor
        video_download = v.get("videoUrl") or v.get("downloadUrl") or v.get("videoDownloadUrl")

        out.append(
            {
                "title": caption,
                "sources": ["tiktok_hashtag"],
                "signals": {
                    "tiktok_hashtag": {
                        "video_url": url,
                        "video_download": video_download,
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