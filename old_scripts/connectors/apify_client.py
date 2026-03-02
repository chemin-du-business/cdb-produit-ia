from __future__ import annotations
import os
from typing import Any, Dict, List
import httpx

APIFY_BASE = "https://api.apify.com/v2"

def _token() -> str:
    tok = (os.environ.get("APIFY_TOKEN") or "").strip()
    if not tok:
        raise RuntimeError("Missing APIFY_TOKEN")
    return tok

def run_actor_get_items(actor_id: str, input_payload: Dict[str, Any], timeout_sec: int = 240, items_limit: int = 50) -> List[Dict[str, Any]]:
    tok = _token()
    url = f"{APIFY_BASE}/acts/{actor_id}/run-sync-get-dataset-items"
    params = {"token": tok, "timeout": str(timeout_sec), "limit": str(items_limit)}
    with httpx.Client(timeout=timeout_sec + 30) as client:
        r = client.post(url, params=params, json=input_payload)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data["items"]
        return []