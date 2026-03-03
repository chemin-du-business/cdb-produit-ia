import requests
from typing import Optional, Tuple


def download_image_bytes(url: str) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        content_type = r.headers.get("content-type")
        return r.content, content_type
    except Exception:
        return None, None