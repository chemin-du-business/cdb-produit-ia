from __future__ import annotations
import os
import mimetypes
from typing import Optional, Tuple
import httpx

def _bucket() -> str:
    return os.environ.get("SUPABASE_IMAGE_BUCKET", "product-images")

def _guess_ext(content_type: str, url: str) -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        if (url or "").lower().endswith(ext):
            return ext
    return ".jpg"

def download_image(url: str, timeout: int = 20) -> Tuple[Optional[bytes], Optional[str]]:
    if not url:
        return None, None
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True)
        if r.status_code >= 400:
            return None, None
        content_type = r.headers.get("content-type") or "image/jpeg"
        return r.content, content_type
    except Exception:
        return None, None

def upload_image_to_supabase(sb, slug: str, image_bytes: bytes, content_type: str, source: str = "pinterest") -> Optional[str]:
    if not image_bytes:
        return None

    bucket = _bucket()
    ext = _guess_ext(content_type or "", "")
    path = f"{source}/{slug}{ext}"

    try:
        sb.storage.from_(bucket).upload(
            path=path,
            file=image_bytes,
            file_options={"content-type": content_type or "image/jpeg", "upsert": "true"},
        )
    except Exception:
        try:
            sb.storage.from_(bucket).upload(
                path, image_bytes, {"content-type": content_type or "image/jpeg", "upsert": "true"}
            )
        except Exception:
            return None

    try:
        pub = sb.storage.from_(bucket).get_public_url(path)
        if isinstance(pub, str):
            return pub
        if isinstance(pub, dict) and "publicUrl" in pub:
            return pub["publicUrl"]
        if isinstance(pub, dict) and "data" in pub and isinstance(pub["data"], dict) and "publicUrl" in pub["data"]:
            return pub["data"]["publicUrl"]
    except Exception:
        pass

    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if supabase_url:
        return f"{supabase_url}/storage/v1/object/public/{bucket}/{path}"
    return None