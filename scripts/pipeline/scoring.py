from __future__ import annotations
from typing import Dict, Any, List

def score_candidate(c: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score /100 simple V1:
    - +40 si présent sur Trends (et plus si intérêt élevé)
    - +20 si présent Pinterest
    - +20 si présent TikTok
    - +20 bonus si multi-sources
    """
    sources: List[str] = c.get("sources", [])
    breakdown = {"trends": 0, "pinterest": 0, "tiktok": 0, "multi": 0}

    if "google_trends" in sources:
        interest = int(c.get("signals", {}).get("google_trends", {}).get("interest", 0) or 0)
        breakdown["trends"] = min(40, max(10, interest // 3))  # rough

    if "pinterest" in sources:
        breakdown["pinterest"] = 20

    if "tiktok" in sources:
        breakdown["tiktok"] = 20

    if len(set(sources)) >= 2:
        breakdown["multi"] = 20

    score = sum(breakdown.values())
    score = max(0, min(100, score))
    return {"score": score, "score_breakdown": breakdown}