from __future__ import annotations
from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def clamp(n: int, a: int, b: int) -> int:
    return max(a, min(b, n))