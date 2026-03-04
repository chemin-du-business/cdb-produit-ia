from __future__ import annotations
from typing import Any, Dict, List


def _clamp(x: int, a: int, b: int) -> int:
    return max(a, min(b, x))


def score_candidate(c: Dict[str, Any]) -> Dict[str, Any]:
    sources: List[str] = c.get("sources", []) or []
    signals = c.get("signals") or {}

    breakdown = {"tiktok": 0, "pinterest": 0, "multi": 0}

    if "tiktok_cc" in sources:
        tt = (signals.get("tiktok_cc") or {})
        rank = int(tt.get("rank", 999) or 999)
        posts = int(tt.get("posts", 0) or 0)

        rank_score = int(max(0, 40 - (rank - 1) * (40 / 99))) if rank <= 100 else 0

        if posts >= 5_000_000:
            posts_score = 30
        elif posts >= 1_000_000:
            posts_score = 25
        elif posts >= 300_000:
            posts_score = 20
        elif posts >= 100_000:
            posts_score = 15
        elif posts >= 30_000:
            posts_score = 10
        elif posts >= 10_000:
            posts_score = 5
        else:
            posts_score = 0

        breakdown["tiktok"] = _clamp(rank_score + posts_score, 0, 70)

    if "pinterest" in sources:
        pin = (signals.get("pinterest") or {})
        hits = int(pin.get("hits", 0) or 0)
        breakdown["pinterest"] = _clamp(hits, 0, 20)

    if len(set(sources)) >= 2:
        breakdown["multi"] = 10

    score = _clamp(sum(breakdown.values()), 0, 100)
    return {"score": score, "score_breakdown": breakdown}
