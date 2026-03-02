import os
from typing import Any, Dict, List, Optional
from supabase import create_client, Client


def _sb() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


def upsert_product(row: Dict[str, Any]) -> None:
    sb = _sb()
    # upsert by unique slug
    sb.table("products").upsert(row, on_conflict="slug").execute()


def upsert_run(run_date: str, status: str, stats: Dict[str, Any], errors: List[Dict[str, Any]]) -> None:
    sb = _sb()
    payload = {
        "run_date": run_date,
        "status": status,
        "stats": stats,
        "errors": errors,
    }
    sb.table("runs").upsert(payload, on_conflict="run_date").execute()


def upload_image_to_storage(slug: str, image_bytes: bytes, content_type: str) -> Optional[str]:
    """
    Uploads the downloaded image bytes to Supabase Storage and returns a public URL.
    """
    sb = _sb()
    bucket = os.environ.get("SUPABASE_BUCKET", "product-images")

    # path in bucket
    ext = "jpg"
    if "png" in (content_type or "").lower():
        ext = "png"
    path = f"{slug}.{ext}"

    # upload (upsert)
    sb.storage.from_(bucket).upload(
        path=path,
        file=image_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )

    # public URL
    pub = sb.storage.from_(bucket).get_public_url(path)
    return pub