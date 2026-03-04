from __future__ import annotations

import math
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


def _log_norm(x: float, maxv: float) -> float:
    """
    Normalisation log pour éviter qu’un outlier écrase tout.
    retourne 0..1
    """
    if x <= 0 or maxv <= 0:
        return 0.0
    # log1p pour stabilité
    return _clamp(math.log1p(x) / math.log1p(maxv), 0.0, 1.0)


def _recency_score(created_at_iso: Any) -> int:
    """
    0..20 (plus généreux)
    """
    d = _parse_iso(created_at_iso)
    if not d:
        return 6  # si inconnu, on donne un petit score au lieu de 0 (sinon ça plombe)
    now = datetime.now(timezone.utc)
    days = (now - d).total_seconds() / 86400.0

    if days <= 2:
        return 20
    if days <= 5:
        return 17
    if days <= 10:
        return 14
    if days <= 20:
        return 10
    if days <= 45:
        return 7
    if days <= 120:
        return 4
    return 2


def score_candidate(
    c: Dict[str, Any],
    max_views: int,
    max_likes: int,
    max_shares: int,
) -> Dict[str, Any]:
    """
    TikTok-only score 0..100 (plus "spread")
    Breakdown:
      - reach/views (0..35)      [log-norm]
      - engagement (0..25)       [like+comment+share rate]
      - virality (0..20)         [shares + share_rate]
      - recency (0..15)
      - quality (0..5)           [duration + like_rate]
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
        like_rate = likes / float(views)
    else:
        engagement_rate = 0.0
        share_rate = 0.0
        like_rate = 0.0

    # 1) Reach/views: 0..35 (log)
    reach = int(round(_log_norm(views, float(max_views)) * 35))

    # 2) Engagement: 0..25
    # 6% engagement => max (un peu plus facile à atteindre)
    eng = int(round(_clamp(engagement_rate / 0.06, 0.0, 1.0) * 25))

    # 3) Virality: 0..20 (mix shares log + share_rate)
    shares_part = _log_norm(shares, float(max_shares))  # 0..1
    # 0.8% share rate => max (viral)
    share_rate_part = _clamp(share_rate / 0.008, 0.0, 1.0)
    virality = int(round((0.65 * shares_part + 0.35 * share_rate_part) * 20))

    # 4) Recency: 0..15 (plus léger que V1)
    rec = int(round(_clamp(_recency_score(created_at) / 20.0, 0.0, 1.0) * 15))

    # 5) Quality: 0..5
    # duration bonus si 6..35s
    dur_ok = 1.0 if (6 <= duration <= 35) else 0.6 if duration else 0.7
    # like_rate 3% => max
    like_ok = _clamp(like_rate / 0.03, 0.0, 1.0)
    quality = int(round(_clamp(0.6 * dur_ok + 0.4 * like_ok, 0.0, 1.0) * 5))

    breakdown = {
        "reach": reach,
        "engagement": eng,
        "virality": virality,
        "recency": rec,
        "quality": quality,
        "engagement_rate": round(engagement_rate, 4),
        "share_rate": round(share_rate, 4),
        "like_rate": round(like_rate, 4),
    }

    score = reach + eng + virality + rec + quality
    score = max(0, min(100, int(score)))

    return {"score": score, "score_breakdown": breakdown}