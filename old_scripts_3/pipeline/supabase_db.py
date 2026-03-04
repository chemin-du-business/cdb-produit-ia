from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from supabase import create_client, Client


def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    return create_client(url, key)


def upsert_products(sb: Client, rows: List[Dict[str, Any]]) -> None:
    """
    Upsert on products.slug (unique)
    Important: ne pas appeler Supabase si rows est vide (sinon erreur PGRST100).
    """
    if not rows:
        print("⚠️ upsert_products: no rows to upsert (skipping)")
        return

    sb.table("products").upsert(rows, on_conflict="slug").execute()


def set_current_run_date(sb: Client, run_date: str) -> None:
    """
    settings: key = 'current_run_date', value stocké en json {"v": "..."} (comme tu as déjà)
    """
    sb.table("settings").upsert(
        {"key": "current_run_date", "value": {"v": run_date}},
        on_conflict="key",
    ).execute()


def insert_run_log(
    sb: Client,
    run_date: str,
    status: str,
    stats: Dict[str, Any],
    errors: Dict[str, Any],
) -> None:
    """
    runs: upsert par run_date
    """
    sb.table("runs").upsert(
        {
            "run_date": run_date,
            "status": status,
            "stats": stats or {},
            "errors": errors or {},
        },
        on_conflict="run_date",
    ).execute()


def get_setting(sb: Client, key: str, default: Optional[Any] = None) -> Any:
    res = sb.table("settings").select("value").eq("key", key).limit(1).execute()

    if res.data and len(res.data) > 0:
        val = res.data[0].get("value")
        if isinstance(val, dict):
            return val.get("v", default)
        return val if val is not None else default

    return default