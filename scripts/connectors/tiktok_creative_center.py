from __future__ import annotations

import requests
from typing import Any, Dict, List


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121 Safari/537.36"


API_URL = "https://ads.tiktok.com/creative_radar_api/v1/popular_hashtags"


def fetch_tiktok_creative_center_candidates(region: str = "FR", limit: int = 120) -> List[Dict[str, Any]]:
    """
    V2 stable :
    utilise l'API interne Creative Center
    """

    params = {
        "country_code": region,
        "period": "7",
        "limit": limit
    }

    try:
        r = requests.get(
            API_URL,
            params=params,
            headers={"User-Agent": UA},
            timeout=20,
        )

        data = r.json()

        items = data.get("data", {}).get("list", [])

        out: List[Dict[str, Any]] = []

        for i, item in enumerate(items):

            tag = item.get("hashtag_name") or ""
            posts = int(item.get("video_cnt", 0) or 0)

            if not tag:
                continue

            title = tag.replace("#", "").replace("_", " ").strip()

            out.append(
                {
                    "title": title,
                    "sources": ["tiktok_cc"],
                    "signals": {
                        "tiktok_cc": {
                            "type": "hashtag",
                            "rank": i + 1,
                            "posts": posts,
                            "source_url": "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag",
                        }
                    },
                }
            )

        return out

    except Exception:
        return []