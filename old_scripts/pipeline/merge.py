from __future__ import annotations
from typing import Any, Dict, List

def merge_candidates(cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}

    for c in cands:
        title = (c.get("title") or "").strip()
        if not title:
            continue

        key = title.lower()

        if key not in merged:
            merged[key] = {
                "title": title,
                "sources": [],
                "signals": {},
                "tags": c.get("tags") or [],
                "category": c.get("category"),
                "image_url": c.get("image_url"),
                "image_source": c.get("image_source"),
                "source_url": c.get("source_url"),
            }

        for s in (c.get("sources") or []):
            if s not in merged[key]["sources"]:
                merged[key]["sources"].append(s)

        sig = c.get("signals") or {}
        if isinstance(sig, dict):
            merged[key]["signals"].update(sig)

        if c.get("image_url") and not merged[key].get("image_url"):
            merged[key]["image_url"] = c.get("image_url")
            merged[key]["image_source"] = c.get("image_source")
            merged[key]["source_url"] = c.get("source_url")

    return list(merged.values())