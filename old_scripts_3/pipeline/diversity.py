from __future__ import annotations
from typing import Any, Dict, List

def apply_category_diversity(sorted_items: List[Dict[str, Any]], max_per_category: int = 3) -> List[Dict[str, Any]]:
    counts = {}
    out = []
    for p in sorted_items:
        cat = (p.get("category") or "autre").lower()
        counts.setdefault(cat, 0)
        if counts[cat] >= max_per_category:
            continue
        out.append(p)
        counts[cat] += 1
    return out