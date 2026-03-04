from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
from supabase import Client, create_client


def get_supabase() -> Client:
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


def upload_video(sb, video_url: str, path: str):
    if not video_url:
        return None

    r = requests.get(video_url, timeout=60)
    r.raise_for_status()

    sb.storage.from_("video-public").upload(
        path,
        r.content,
        file_options={"content-type": "video/mp4", "upsert": "true"},
    )

    return sb.storage.from_("video-public").get_public_url(path)


def upsert_products(sb: Client, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    sb.table("products").upsert(rows, on_conflict="slug").execute()