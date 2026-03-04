from __future__ import annotations
import os
from typing import Any, Dict, List
from supabase import create_client, Client

def get_supabase() -> Client:
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

def upsert_products(sb: Client, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    sb.table("products").upsert(rows, on_conflict="slug").execute()
