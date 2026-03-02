from typing import Any, Dict
from scripts.pipeline.utils import safe_int


def _clip(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def score_candidate(item: Dict[str, Any]) -> Dict[str, Any]:
    signals = item.get("signals", {})

    gt = signals.get("google_trends", {}) if isinstance(signals.get("google_trends"), dict) else {}
    tt = signals.get("tiktok", {}) if isinstance(signals.get("tiktok"), dict) else {}
    pin = signals.get("pinterest", {}) if isinstance(signals.get("pinterest"), dict) else {}

    # --- Google Trends component (0-35)
    interest = safe_int(gt.get("interest_score", 0))
    peak = safe_int(gt.get("peak", 0))
    slope = float(gt.get("slope", 0) or 0)

    gt_score = _clip((interest * 0.6) + (peak * 0.2) + (max(0.0, slope) * 10.0), 0, 35)

    # --- TikTok component (0-40)
    posts = safe_int(tt.get("posts", 0))
    views_med = safe_int(tt.get("views_median", 0))
    views_top = safe_int(tt.get("views_top", 0))
    likes_med = safe_int(tt.get("likes_median", 0))

    # normalize views roughly (log-ish without log):
    # 10k-> ok, 100k-> strong, 1M-> very strong
    def norm_views(v: int) -> float:
        if v <= 0:
            return 0
        if v < 10_000:
            return v / 10_000 * 10
        if v < 100_000:
            return 10 + (v - 10_000) / 90_000 * 15
        if v < 1_000_000:
            return 25 + (v - 100_000) / 900_000 * 10
        return 35

    tt_score = _clip(
        norm_views(views_med) + norm_views(views_top) * 0.5 + _clip(posts, 0, 20) * 0.3,
        0, 40
    )

    # penalty if "too viral" but weak engagement (rough)
    # if top views huge but likes median very low -> suspicious / oversaturated
    penalty = 0
    if views_top > 2_000_000 and likes_med < 2000:
        penalty += 6
    if views_top > 5_000_000:
        penalty += 4

    # --- Pinterest component (0-25)
    pins = safe_int(pin.get("pins", 0))
    pinner_fc_med = safe_int(pin.get("pinner_followers_median", 0))

    pin_score = _clip((pins / 30) * 15 + _clip(pinner_fc_med / 1000, 0, 10), 0, 25)

    total = int(_clip(gt_score + tt_score + pin_score - penalty, 0, 100))

    item["score"] = total
    item["score_breakdown"] = {
        "google_trends": round(gt_score, 2),
        "tiktok": round(tt_score, 2),
        "pinterest": round(pin_score, 2),
        "penalty": penalty,
        "total": total,
    }
    return item