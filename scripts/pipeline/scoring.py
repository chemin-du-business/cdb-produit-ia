from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _safe_int(x: Any) -> int:
    try:
        return int(x or 0)
    except Exception:
        return 0


def _parse_iso(dt: Any) -> Optional[datetime]:
    if not dt:
        return None
    try:
        s = str(dt).strip()
        # support "...Z"
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _norm(x: float, maxv: float) -> float:
    if maxv <= 0:
        return 0.0
    return _clamp(x / maxv, 0.0, 1.0)


def _recency_score(created_at_iso: Any) -> int:
    """
    0..20
    0 si vieux, 20 si très récent.
    Paliers simples (robuste).
    """
    d = _parse_iso(created_at_iso)
    if not d:
        return 0

    now = datetime.now(timezone.utc)
    days = (now - d).total_seconds() / 86400.0

    if days <= 3:
        return 20
    if days <= 7:
        return 16
    if days <= 14:
        return 12
    if days <= 30:
        return 8
    if days <= 90:
        return 4
    return 0


def score_candidate(
    c: Dict[str, Any],
    max_views: int,
    max_likes: int,
    max_shares: int,
) -> Dict[str, Any]:
    """
    TikTok-only score 0..100
    Breakdown:
      - views (0..30)
      - engagement (0..25)
      - shares (0..15)
      - recency (0..20)
      - quality (0..10) (durée + ratio)
    """
    signals = c.get("signals") or {}
    tk = (signals.get("tiktok_hashtag") or {})

    views = _safe_int(tk.get("views"))
    likes = _safe_int(tk.get("likes"))
    shares = _safe_int(tk.get("shares"))
    comments = _safe_int(tk.get("comments"))
    duration = _safe_int(tk.get("duration_seconds"))
    created_at = tk.get("created_at")

    # ratios
    if views > 0:
        engagement_rate = (likes + comments + shares) / float(views)  # 0..1+
        share_rate = shares / float(views)
    else:
        engagement_rate = 0.0
        share_rate = 0.0

    # ---------- sub-scores ----------
    # Views 0..30
    views_score = int(round(_norm(views, float(max_views)) * 30))

    # Shares 0..15 (mix norm + ratio)
    shares_norm = _norm(shares, float(max_shares))  # 0..1
    share_ratio_boost = _clamp(share_rate / 0.01, 0.0, 1.0)  # 1% share rate => max
    shares_score = int(round((0.7 * shares_norm + 0.3 * share_ratio_boost) * 15))

    # Engagement 0..25
    # 8% engagement => max (au-delà clamp)
    engagement_score = int(round(_clamp(engagement_rate / 0.08, 0.0, 1.0) * 25))

    # Recency 0..20
    recency = _recency_score(created_at)

    # Quality 0..10 (vidéos courtes performantes)
    # bonus si duration 6..35s (format UGC)
    dur_ok = 1.0 if (6 <= duration <= 35) else 0.4 if duration else 0.6
    # bonus léger si like/view ratio ok (>=3%)
    like_rate = (likes / float(views)) if views > 0 else 0.0
    like_ok = _clamp(like_rate / 0.03, 0.0, 1.0)
    quality = int(round(_clamp(0.6 * dur_ok + 0.4 * like_ok, 0.0, 1.0) * 10))

    breakdown = {
        "views": views_score,
        "engagement": engagement_score,
        "shares": shares_score,
        "recency": recency,
        "quality": quality,
        # debug ratios (optionnel, utile à afficher dans l'app)
        "engagement_rate": round(engagement_rate, 4),
        "share_rate": round(share_rate, 4),
    }

    score = views_score + engagement_score + shares_score + recency + quality
    score = max(0, min(100, int(score)))

    return {"score": score, "score_breakdown": breakdown}