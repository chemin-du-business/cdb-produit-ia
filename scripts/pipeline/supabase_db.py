from __future__ import annotations
import os
from typing import Any, Dict, List
from supabase import create_client, Client

def get_supabase() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

def upsert_products(sb: Client, rows: List[Dict[str, Any]]) -> None:
    sb.table("products").upsert(rows, on_conflict="slug").execute()

def set_current_run(sb: Client, run_date: str, mode: str) -> None:
    # settings.value is jsonb
    sb.table("settings").upsert(
        {"key": "current_run", "value": {"run_date": run_date, "mode": mode}},
        on_conflict="key",
    ).execute()

def insert_run_log(sb: Client, run_date: str, status: str, stats: Dict[str, Any], errors: Dict[str, Any]) -> None:
    # runs unique(run_date)
    sb.table("runs").upsert(
        {"run_date": run_date, "status": status, "stats": stats, "errors": errors},
        on_conflict="run_date",
    ).execute()