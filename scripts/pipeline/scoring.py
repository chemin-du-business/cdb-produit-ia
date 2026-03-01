from __future__ import annotations
from typing import Any, Dict, List

MONETIZATION_KEYWORDS = [
    "kit", "set", "pack", "starter", "pro", "premium",
    "appareil", "machine", "dispositif", "système", "systeme",
    "lampe", "projecteur", "aspirateur", "diffuseur",
    "outil", "pistolet", "brosse", "tondeuse", "mousseur",
    "support", "organisateur", "rangement", "étagère", "etagere",
    "chargeur", "station", "dock", "magnétique", "magnetique",
]

SATURATION_BLOCK = [
    "iphone", "samsung", "ps5", "xbox", "playstation", "macbook",
    "netflix", "disney", "tesla", "airpods",
]

def compute_max_interest(cands: List[Dict[str, Any]]) -> int:
    m = 0
    for c in cands:
        gt = (c.get("signals") or {}).get("google_trends", {}) or {}
        interest = int(gt.get("interest", 0) or 0)
        if interest > m:
            m = interest
    return m or 100

def _safe_int(x: Any) -> int:
    try:
        return int(x or 0)
    except Exception:
        return 0

def _contains_any(title: str, words: List[str]) -> bool:
    t = (title or "").lower()
    return any(w in t for w in words)

def score_candidate(c: Dict[str, Any], max_interest: int) -> Dict[str, Any]:
    title = c.get("title") or ""
    sources: List[str] = c.get("sources", []) or []
    signals = c.get("signals") or {}

    breakdown = {
        "trends": 0,
        "momentum": 0,
        "pinterest": 0,
        "tiktok": 0,
        "repeatability": 0,
        "monetization": 0,
        "saturation_penalty": 0,
        "multi": 0,
    }

    # Google Trends (0..35) + momentum (0..7)
    if "google_trends" in sources:
        gt = signals.get("google_trends", {}) or {}
        interest = _safe_int(gt.get("interest", 0))
        kind = (gt.get("kind") or "").lower()
        breakdown["trends"] = round((interest / max_interest) * 35)
        if "rising" in kind:
            breakdown["momentum"] = 7
        elif "top" in kind:
            breakdown["momentum"] = 4

    # Pinterest (0..18)
    pin = signals.get("pinterest", {}) or {}
    pin_count = _safe_int(pin.get("pin_count", 0))
    saves = _safe_int(pin.get("save_count", 0)) + _safe_int(pin.get("repin_count", 0))
    breakdown["pinterest"] = min(18, min(12, pin_count // 2) + min(6, saves // 100))

    # TikTok (0..18)
    tk = signals.get("tiktok", {}) or {}
    views = _safe_int(tk.get("views", 0))
    likes = _safe_int(tk.get("likes", 0))
    comments = _safe_int(tk.get("comments", 0))
    shares = _safe_int(tk.get("shares", 0))
    video_count = _safe_int(tk.get("video_count", 0))

    volume_pts = min(10, views // 200_000)
    eng_pts = 0
    if views > 0 and (likes + comments + shares) > 0:
        eng = (likes + 2 * comments + 3 * shares) / max(1, views)
        eng_pts = min(8, int(eng * 100))
    breakdown["tiktok"] = min(18, volume_pts + min(8, eng_pts))

    # Repeatability (0..10)
    rep_tk = min(6, video_count // 10)
    rep_pin = min(4, pin_count // 10)
    breakdown["repeatability"] = rep_tk + rep_pin

    # Monetization (0..7)
    breakdown["monetization"] = 7 if _contains_any(title, MONETIZATION_KEYWORDS) else 0

    # Saturation penalty (-10..0)
    penalty = 0
    if _contains_any(title, SATURATION_BLOCK):
        penalty = -10
    if views >= 5_000_000:
        eng = (likes + 2 * comments + 3 * shares) / max(1, views) if (likes + comments + shares) > 0 else 0
        if eng < 0.01:
            penalty = min(penalty, -6)
    breakdown["saturation_penalty"] = penalty

    # Multi-source bonus (0..5)
    if len(set(sources)) >= 2:
        breakdown["multi"] = 5

    score = (
        breakdown["trends"]
        + breakdown["momentum"]
        + breakdown["pinterest"]
        + breakdown["tiktok"]
        + breakdown["repeatability"]
        + breakdown["monetization"]
        + breakdown["multi"]
        + breakdown["saturation_penalty"]
    )
    score = max(0, min(100, int(score)))
    return {"score": score, "score_breakdown": breakdown}