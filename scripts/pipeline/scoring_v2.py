"""Scoring multi-sources V2 — combine TikTok + Amazon + Meta + Google + TikTok Shop."""
from __future__ import annotations

import math
from typing import Any, Dict


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _log_norm(x: float, maxv: float) -> float:
    if x <= 0 or maxv <= 0:
        return 0.0
    return _clamp(math.log1p(x) / math.log1p(maxv))


def score_candidate_v2(
    candidate: Dict[str, Any],
    max_views: int = 1,
    max_likes: int = 1,
    max_shares: int = 1,
) -> Dict[str, Any]:
    """
    Score multi-sources 0..100.

    Pondération :
      - TikTok viral (hashtag + discover) : 40 pts
      - Amazon (demande marché)            : 20 pts
      - Google (trends + shopping)         : 20 pts
      - Meta Ads (validation pub)          : 10 pts
      - TikTok Shop (ventes réelles)       : 10 pts

    Un candidat sans signal sur une source reçoit 0 sur cette source.
    """
    signals = candidate.get("signals", {}) or {}

    # ── TikTok (40 pts) ─────────────────────────────────────────────────────
    tiktok_score = _score_tiktok(signals, max_views, max_likes, max_shares)   # 0..40

    # ── Amazon (20 pts) ─────────────────────────────────────────────────────
    amz = signals.get("amazon") or {}
    amazon_score = int(round(_clamp(amz.get("demand_score", 0) / 100.0) * 20))

    # ── Google (20 pts = Trends 10 + Shopping 10) ───────────────────────────
    trends = signals.get("google_trends") or {}
    shopping = signals.get("google_shopping") or {}

    trends_raw = trends.get("current_value", 0) or 0  # 0..100 (Google scale)
    trends_direction_bonus = {"rising": 1.0, "stable": 0.7, "declining": 0.4, "unknown": 0.5}
    trends_direction = trends.get("trend_direction", "unknown")
    trends_score = int(round(_clamp(trends_raw / 100.0) * trends_direction_bonus.get(trends_direction, 0.5) * 10))

    shop_raw = shopping.get("market_score", 0) or 0
    shopping_score = int(round(_clamp(shop_raw / 100.0) * 10))

    google_score = trends_score + shopping_score   # 0..20

    # ── Meta Ads (10 pts) ───────────────────────────────────────────────────
    meta = signals.get("meta_ads") or {}
    meta_score = int(round(_clamp((meta.get("ad_validation_score", 0) or 0) / 100.0) * 10))

    # ── TikTok Shop (10 pts) ────────────────────────────────────────────────
    tshop = signals.get("tiktok_shop") or {}
    tshop_score = int(round(_clamp((tshop.get("shop_score", 0) or 0) / 100.0) * 10))

    # ── Total ───────────────────────────────────────────────────────────────
    total = tiktok_score + amazon_score + google_score + meta_score + tshop_score
    total = max(0, min(100, total))

    # Statut tendance basé sur le score + direction Google Trends
    status = _infer_status(total, trends_direction, signals)

    return {
        "score": total,
        "status": status,
        "score_breakdown": {
            "tiktok": tiktok_score,
            "amazon": amazon_score,
            "google_trends": trends_score,
            "google_shopping": shopping_score,
            "meta_ads": meta_score,
            "tiktok_shop": tshop_score,
        },
    }


def _score_tiktok(signals: Dict, max_views: int, max_likes: int, max_shares: int) -> int:
    """Score TikTok combiné hashtag + discover sur 40 pts."""
    tk_hash = signals.get("tiktok_hashtag") or {}
    tk_disc = signals.get("tiktok_discover") or {}

    # Hashtag signals
    views = int(tk_hash.get("views") or 0)
    likes = int(tk_hash.get("likes") or 0)
    shares = int(tk_hash.get("shares") or 0)
    comments = int(tk_hash.get("comments") or 0)

    if views > 0:
        eng_rate = (likes + comments + shares) / float(views)
        share_rate = shares / float(views)
    else:
        eng_rate = 0.0
        share_rate = 0.0

    reach = _clamp(_log_norm(views, max_views)) * 15        # 0..15
    engagement = _clamp(eng_rate / 0.06) * 10               # 0..10
    virality = _clamp(share_rate / 0.008) * 8               # 0..8

    # Discover signal (boost)
    discover_viral = tk_disc.get("viral_score", 0) or 0
    discover_boost = _clamp(discover_viral / 100.0) * 7    # 0..7

    tiktok_total = int(round(reach + engagement + virality + discover_boost))
    return max(0, min(40, tiktok_total))


def _infer_status(score: int, trend_direction: str, signals: Dict) -> str:
    """
    Statuts : Émergent | En tendance | Populaire | En regain | En déclin
    """
    shop_score = (signals.get("tiktok_shop") or {}).get("shop_score", 0) or 0
    amz_score = (signals.get("amazon") or {}).get("demand_score", 0) or 0

    if trend_direction == "declining":
        return "En déclin"

    if trend_direction == "rising" and score < 50:
        return "Émergent"

    if trend_direction == "rising" and score >= 50:
        return "En tendance"

    if trend_direction == "stable" and (shop_score > 50 or amz_score > 50):
        return "Populaire"

    if trend_direction == "stable" and score >= 60:
        return "En regain"

    if score >= 70:
        return "Populaire"

    if score >= 50:
        return "En tendance"

    return "Émergent"
