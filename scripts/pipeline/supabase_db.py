from __future__ import annotations

import os
import mimetypes
from typing import Any, Dict, List, Optional

import requests
from supabase import create_client, Client


def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def upsert_products(sb: Client, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    sb.table("products").upsert(rows, on_conflict="slug").execute()


def _video_bucket() -> str:
    # ton bucket: video--public
    return (os.environ.get("SUPABASE_VIDEO_BUCKET") or "video--public").strip()


def upload_video(sb: Client, video_url: str, path: str) -> Optional[str]:
    """
    Télécharge la vidéo (URL Apify/TT), l'upload dans Supabase Storage,
    et retourne l'URL publique.
    """
    if not video_url or not path:
        return None

    bucket = _video_bucket()

    # 1) Download video
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    r = requests.get(video_url, headers=headers, stream=True, timeout=60)
    r.raise_for_status()

    # Sécurité anti-fichiers énormes (modifiable)
    max_bytes = int(os.environ.get("VIDEO_MAX_BYTES") or str(80 * 1024 * 1024))  # 80MB
    chunks: List[bytes] = []
    total = 0

    for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes:
            raise RuntimeError(f"Vidéo trop grosse: {total} bytes > {max_bytes}")
        chunks.append(chunk)

    data = b"".join(chunks)

    # 2) Upload to Supabase Storage
    content_type, _ = mimetypes.guess_type(path)
    if not content_type:
        content_type = "video/mp4"

    # supabase-py: upload(path, file, file_options={...})
    sb.storage.from_(bucket).upload(
        path=path,
        file=data,
        file_options={
            "content-type": content_type,
            "upsert": "true",
        },
    )

    # 3) Public URL
    public = sb.storage.from_(bucket).get_public_url(path)
    return public