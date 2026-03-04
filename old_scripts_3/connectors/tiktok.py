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

        r = requests.get(
            url,
            headers={
                "User-Agent": UA,
                "Accept-Language": "en-US,en;q=0.9"
            },
            timeout=20
        )

        html = r.text or ""

        # détecter vidéos
        hits = len(re.findall(r'"type":"video"', html))

        # récupérer les playCount (vues)
        plays = re.findall(r'"playCount":(\d+)', html)

        views_estimate = 0

        if plays:
            # moyenne des vues trouvées
            nums = [int(x) for x in plays[:10]]
            views_estimate = sum(nums) // len(nums)

        # fallback si aucun playCount détecté
        if views_estimate == 0:
            tokens = len(re.findall(r'"playCount"', html))
            views_estimate = tokens * 100_000

        return {
            "hits": hits,
            "views_estimate": views_estimate,
            "source_url": url
        }

    except Exception as e:

        print("TikTok error:", e)

        return {
            "hits": 0,
            "views_estimate": 0,
            "source_url": url
        }