from __future__ import annotations
from typing import Any, Dict, List

def apply_category_diversity(items_sorted: List[Dict[str, Any]], max_per_category: int = 3) -> List[Dict[str, Any]]:
    counts = {}
    out = []

    for item in items_sorted:
        cat = (item.get("category") or "autre").lower()
        counts.setdefault(cat, 0)

        if counts[cat] >= max_per_category:
            continue

        out.append(item)
        counts[cat] += 1

    return out