from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlencode

import requests
from playwright.sync_api import sync_playwright


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"
)

PAD_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pad/en"
API_URL = "https://ads.tiktok.com/creative_radar_api/v1/popular_trend/hashtag/list"


def _get_cc_headers(region: str = "FR") -> Dict[str, str]:

    needed = {"anonymous-user-id", "timestamp", "user-sign"}
    captured: Dict[str, str] = {}

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=UA,
            locale="fr-FR",
            extra_http_headers={"Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7"},
        )

        page = context.new_page()

        def on_request(req):

            nonlocal captured

            url = req.url or ""

            if "creative_radar_api" in url:

                h = {k.lower(): v for k, v in (req.headers or {}).items()}

                for k in list(needed):

                    if k in h and h[k]:

                        captured[k] = h[k]

        page.on("request", on_request)

        qs = urlencode({"country_code": region, "region": region})

        page.goto(f"{PAD_URL}?{qs}", wait_until="domcontentloaded", timeout=60000)

        page.wait_for_timeout(6000)

        context.close()

        browser.close()

    if not needed.issubset(captured.keys()):

        return {}

    return {
        "anonymous-user-id": captured["anonymous-user-id"],
        "timestamp": captured["timestamp"],
        "user-sign": captured["user-sign"],
    }


def fetch_tiktok_creative_center_candidates(region: str = "FR", limit: int = 100) -> List[Dict[str, Any]]:

    headers = _get_cc_headers(region=region)

    if not headers:

        return []

    params = {
        "page": 1,
        "limit": min(limit, 100),
        "period": "7",
        "country_code": region,
        "sort_by": "popular",
    }

    try:

        r = requests.get(
            API_URL,
            params=params,
            headers={
                "User-Agent": UA,
                "Accept": "application/json",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
                **headers,
            },
            timeout=30,
        )

        data = r.json() if r.content else {}

        lst = ((data.get("data") or {}).get("list") or [])

        out: List[Dict[str, Any]] = []

        for i, item in enumerate(lst, start=1):

            tag = (item.get("hashtag_name") or "").strip()

            if not tag:
                continue

            title = tag.replace("#", "").replace("_", " ").strip()

            posts = int(item.get("video_cnt", 0) or 0)

            out.append(
                {
                    "title": title,
                    "sources": ["tiktok_cc"],
                    "signals": {
                        "tiktok_cc": {
                            "type": "hashtag",
                            "rank": i,
                            "posts": posts,
                            "source_url": "https://ads.tiktok.com/business/creativecenter",
                        }
                    },
                }
            )

        return out

    except Exception:

        return []
