from __future__ import annotations

from typing import Any, Dict, List


def compute_max_interest(cands: List[Dict[str, Any]]) -> int:
    """
    max_interest sert à normaliser l'intérêt Trends.
    Si aucun intérêt, on met 100 pour éviter division par 0.
    """
    m = 0
    for c in cands:
        gt = (c.get("signals") or {}).get("google_trends", {}) or {}
        interest = int(gt.get("interest", 0) or 0)
        if interest > m:
            m = interest
    return m or 100


def score_candidate(c: Dict[str, Any], max_interest: int) -> Dict[str, Any]:
    sources: List[str] = c.get("sources", []) or []
    signals = c.get("signals") or {}

    breakdown = {
        "trends": 0,
        "momentum": 0,
        "pinterest": 0,
        "tiktok": 0,
        "multi": 0,
        "social_penalty": 0,
    }

    # -----------------------
    # Trends (0..40)
    # -----------------------
    gt = (signals.get("google_trends") or {}) if isinstance(signals, dict) else {}
    interest = int(gt.get("interest", 0) or 0)
    kind = (gt.get("kind") or "").lower()

    breakdown["trends"] = max(0, min(40, round((interest / max_interest) * 40)))

    # Momentum (0..20)
    # rising > top > fallback
    if "rising" in kind:
        breakdown["momentum"] = 18
    elif "top" in kind:
        breakdown["momentum"] = 10
    elif "fallback" in kind:
        breakdown["momentum"] = 6

    # -----------------------
    # Pinterest (0..20)
    # hits = proxy
    # -----------------------
    pin_hits = 0
    if "pinterest" in sources:
        pin = signals.get("pinterest", {}) or {}
        pin_hits = int(pin.get("hits", 0) or 0)

    breakdown["pinterest"] = min(20, pin_hits)

    # -----------------------
    # TikTok (0..20)
    # views_estimate = proxy
    # -----------------------
    tk_hits = 0
    tk_views = 0
    if "tiktok" in sources:
        tk = signals.get("tiktok", {}) or {}
        tk_hits = int(tk.get("hits", 0) or 0)
        tk_views = int(tk.get("views_estimate", 0) or 0)

    # proxy: 200k views ~ 1 point, cap 20
    breakdown["tiktok"] = min(20, tk_views // 200_000)

    # -----------------------
    # Multi-source bonus (0..10)
    # - 2 sources => 6
    # - 3 sources => 10
    # -----------------------
    unique_sources = set(sources)
    if len(unique_sources) >= 3:
        breakdown["multi"] = 10
    elif len(unique_sources) == 2:
        breakdown["multi"] = 6

    # -----------------------
    # Pénalité si aucun signal social (Pinterest=0 ET TikTok=0)
    # - on ne veut pas éliminer totalement, mais éviter que Trends seul domine
    # -----------------------
    if (pin_hits == 0) and (tk_hits == 0) and (tk_views == 0):
        breakdown["social_penalty"] = -20

    score = (
        breakdown["trends"]
        + breakdown["momentum"]
        + breakdown["pinterest"]
        + breakdown["tiktok"]
        + breakdown["multi"]
        + breakdown["social_penalty"]
    )

    score = max(0, min(100, int(score)))
    return {"score": score, "score_breakdown": breakdown}