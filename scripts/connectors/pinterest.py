from __future__ import annotations
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"


BAD_IMG_PATTERNS = [
    "profile",
    "avatar",
    "logo",
    "75x75",
    "60x60",
    "favicon",
]


def is_valid_image(url: str) -> bool:

    if not url:
        return False

    if not url.startswith("http"):
        return False

    if "pinimg" not in url:
        return False

    if any(x in url for x in BAD_IMG_PATTERNS):
        return False

    return True


def fetch_pinterest_signal(query: str) -> Dict[str, Any]:

    q = (query or "").strip()

    if not q:
        return {"hits": 0, "image_url": None, "source_url": None}

    url = f"https://www.pinterest.com/search/pins/?q={quote_plus(q)}"

    try:

        r = requests.get(
            url,
            headers={"User-Agent": UA},
            timeout=20
        )

        html = r.text or ""

        soup = BeautifulSoup(html, "lxml")

        images = []

        for img in soup.find_all("img"):

            src = img.get("src") or ""
            srcset = img.get("srcset") or ""

            if is_valid_image(src):
                images.append(src)

            if srcset:

                parts = srcset.split(",")

                for p in parts:

                    u = p.strip().split(" ")[0]

                    if is_valid_image(u):
                        images.append(u)

        # dédupliquer
        images = list(dict.fromkeys(images))

        hits = len(images)

        image_url = images[0] if images else None

        return {
            "hits": hits,
            "image_url": image_url,
            "source_url": url
        }

    except Exception as e:

        print("Pinterest error:", e)

        return {
            "hits": 0,
            "image_url": None,
            "source_url": url
        }