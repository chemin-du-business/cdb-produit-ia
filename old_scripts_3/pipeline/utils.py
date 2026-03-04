from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Any, Dict

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def today_date() -> date:
    return datetime.now(timezone.utc).date()

def safe_get(d: Dict[str, Any], path: str, default=None):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur