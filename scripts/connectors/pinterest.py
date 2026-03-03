from __future__ import annotations
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"

def fetch_pinterest_signal(query: str) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"hits": 0, "image_url": None, "source_url": None}

    url = f"https://www.pinterest.com/search/pins/?q={quote_plus(q)}"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        html = r.text or ""
        soup = BeautifulSoup(html, "lxml")

        imgs = []
        for img in soup.find_all("img"):
            src = img.get("src") or ""
            if src.startswith("http"):
                imgs.append(src)

        # proxy "hits": nombre d'images trouvées sur la page (indicatif, pas exact)
        hits = len(imgs)
        image_url = imgs[0] if imgs else None

        return {"hits": hits, "image_url": image_url, "source_url": url}
    except Exception:
        return {"hits": 0, "image_url": None, "source_url": url}