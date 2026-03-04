from __future__ import annotations
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"

def fetch_pinterest_signal(query: str) -> Dict[str, Any]:
    q=(query or "").strip()
    url=f"https://www.pinterest.com/search/pins/?q={quote_plus(q)}"
    if not q:
        return {"hits":0,"image_url":None,"source_url":url}

    try:
        r=requests.get(url,headers={"User-Agent":UA},timeout=20)
        soup=BeautifulSoup(r.text or "","lxml")
        imgs=[]
        for img in soup.find_all("img"):
            src=img.get("src") or ""
            if src.startswith("http"):
                imgs.append(src)
        return {"hits":len(imgs),"image_url":(imgs[0] if imgs else None),"source_url":url}
    except Exception:
        return {"hits":0,"image_url":None,"source_url":url}
