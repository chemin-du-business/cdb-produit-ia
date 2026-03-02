from typing import Any, Dict, List


def diversify_top_n(items: List[Dict[str, Any]], top_n: int = 10, max_per_category: int = 2) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}

    for it in items:
        cat = (it.get("category") or "autre").strip().lower()
        counts.setdefault(cat, 0)

        if counts[cat] >= max_per_category:
            continue

        out.append(it)
        counts[cat] += 1

        if len(out) >= top_n:
            break

    # if diversity too strict, backfill
    if len(out) < top_n:
        slugs = {x.get("slug") for x in out}
        for it in items:
            if it.get("slug") in slugs:
                continue
            out.append(it)
            if len(out) >= top_n:
                break

    return out