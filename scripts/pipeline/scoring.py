from __future__ import annotations
from typing import Any, Dict, List

def compute_max_interest(cands: List[Dict[str, Any]]) -> int:
    m = 0
    for c in cands:
        gt = (c.get("signals") or {}).get("google_trends", {})
        interest = int(gt.get("interest", 0) or 0)
        if interest > m:
            m = interest
    return m or 100  # avoid div by 0, keep scale

def score_candidate(c: Dict[str, Any], max_interest: int) -> Dict[str, Any]:
    sources: List[str] = c.get("sources", []) or []
    signals = c.get("signals") or {}

    breakdown = {"trends": 0, "momentum": 0, "pinterest": 0, "tiktok": 0, "multi": 0}

    # Trends (0..45)
    if "google_trends" in sources:
        gt = signals.get("google_trends", {}) or {}
        interest = int(gt.get("interest", 0) or 0)
        kind = (gt.get("kind") or "").lower()

        breakdown["trends"] = round((interest / max_interest) * 40)
        if "rising" in kind:
            breakdown["momentum"] = 8
        elif "top" in kind:
            breakdown["momentum"] = 4

    # Pinterest (0..25)
    if "pinterest" in sources:
        pin = signals.get("pinterest", {}) or {}
        hits = int(pin.get("hits", 0) or 0)
        # proxy: 0..25
        breakdown["pinterest"] = min(25, hits)

    # TikTok (0..25)
    if "tiktok" in sources:
        tk = signals.get("tiktok", {}) or {}
        views = int(tk.get("views_estimate", 0) or 0)
        breakdown["tiktok"] = min(25, views // 200_000)

    # Multi-source bonus (0..10)
    if len(set(sources)) >= 2:
        breakdown["multi"] = 10

    score = sum(breakdown.values())
    score = max(0, min(100, score))
    return {"score": score, "score_breakdown": breakdown}