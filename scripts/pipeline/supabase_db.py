from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from supabase import create_client, Client

def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)

def upsert_products(sb: Client, rows: List[Dict[str, Any]]) -> None:
    # upsert on slug (unique)
    sb.table("products").upsert(rows, on_conflict="slug").execute()

def set_current_run_date(sb: Client, run_date: str) -> None:
    sb.table("settings").upsert(
        {"key": "current_run_date", "value": {"v": run_date}},
        on_conflict="key"
    ).execute()

def insert_run_log(sb: Client, run_date: str, status: str, stats: Dict[str, Any], errors: Dict[str, Any]) -> None:
    sb.table("runs").upsert(
        {"run_date": run_date, "status": status, "stats": stats, "errors": errors},
        on_conflict="run_date"
    ).execute()

def get_setting(sb: Client, key: str, default=None):
    res = sb.table("settings").select("value").eq("key", key).limit(1).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]["value"].get("v", default)
    return default