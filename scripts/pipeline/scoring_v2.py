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
    **_kwargs: Any,
) -> Dict[str, Any]:
    """
    Score multi-sources 0..100.

    Pondération (engines disponibles sur plan SerpApi de base) :
      - Amazon (demande marché)            : 35 pts
      - Google Trends (intérêt recherche)  : 30 pts
      - Google Shopping (présence marché)  : 20 pts
      - TikTok Shop (ventes réelles)       : 15 pts
      - TikTok discover / Meta Ads         : bonus 0..10 si dispo

    Un candidat sans signal sur une source reçoit 0 sur cette source.
    """
    signals = candidate.get("signals", {}) or {}

    # ── Amazon (35 pts) ─────────────────────────────────────────────────────
    amz = signals.get("amazon") or {}
    amazon_score = int(round(_clamp(amz.get("demand_score", 0) / 100.0) * 35))

    # ── Google Trends (30 pts) ──────────────────────────────────────────────
    trends = signals.get("google_trends") or {}
    trends_raw = trends.get("current_value", 0) or 0
    trends_peak = trends.get("peak_value", 0) or 0
    # Utilise peak comme référence relative — un produit à 40/100 sur son pic est fort
    effective_value = trends_raw if trends_peak == 0 else min(100, int((trends_raw / max(trends_peak, 1)) * 100 * 0.7 + trends_raw * 0.3))
    trends_direction_bonus = {"rising": 1.0, "stable": 0.85, "declining": 0.5, "unknown": 0.75}
    trends_direction = trends.get("trend_direction", "unknown")
    trends_score = int(round(_clamp(effective_value / 100.0) * trends_direction_bonus.get(trends_direction, 0.75) * 30))

    # ── Google Shopping (20 pts) ────────────────────────────────────────────
    shopping = signals.get("google_shopping") or {}
    shop_raw = shopping.get("market_score", 0) or 0
    shopping_score = int(round(_clamp(shop_raw / 100.0) * 20))

    google_score = trends_score + shopping_score   # 0..50

    # ── TikTok Shop (15 pts) ────────────────────────────────────────────────
    tshop = signals.get("tiktok_shop") or {}
    tshop_score = int(round(_clamp((tshop.get("shop_score", 0) or 0) / 100.0) * 15))

    # ── TikTok Discover bonus (0..10 si dispo) ──────────────────────────────
    tiktok_score = min(10, _score_tiktok(signals, max_views, max_likes, max_shares) // 4)

    # ── Meta Ads bonus (0..5 si dispo) ──────────────────────────────────────
    meta = signals.get("meta_ads") or {}
    meta_score = int(round(_clamp((meta.get("ad_validation_score", 0) or 0) / 100.0) * 5))

    # ── Total ───────────────────────────────────────────────────────────────
    total = amazon_score + google_score + tshop_score + tiktok_score + meta_score
    total = max(0, min(100, total))

    # Statut tendance basé sur le score + direction Google Trends
    status = _infer_status(total, trends_direction, signals)

    return {
        "score": total,
        "status": status,
        "score_breakdown": {
            "amazon": amazon_score,
            "google_trends": trends_score,
            "google_shopping": shopping_score,
            "tiktok_shop": tshop_score,
            "tiktok": tiktok_score,
            "meta_ads": meta_score,
        },
    }


def _score_tiktok(signals: Dict, max_views: int = 1, max_likes: int = 1, max_shares: int = 1) -> int:
    """Score TikTok sur 40 pts — basé sur tiktok_discover (SerpApi, sans Apify)."""
    tk_disc = signals.get("tiktok_discover") or {}

    # Signaux agrégés depuis le discover
    total_views = int(tk_disc.get("total_views") or 0)
    total_likes = int(tk_disc.get("total_likes") or 0)
    total_shares = int(tk_disc.get("total_shares") or 0)
    posts_count = int(tk_disc.get("posts_count") or 0)
    avg_engagement = float(tk_disc.get("avg_engagement_rate") or 0)
    viral_score = float(tk_disc.get("viral_score") or 0)

    # Reach — vues relatives à la population de candidats
    max_v = max(max_views, total_views, 1)
    reach = _clamp(_log_norm(total_views, max_v)) * 15       # 0..15

    # Engagement rate
    engagement = _clamp(avg_engagement / 0.06) * 10          # 0..10

    # Viralité — partages relatifs
    if total_views > 0:
        share_rate = total_shares / float(total_views)
    else:
        share_rate = 0.0
    virality = _clamp(share_rate / 0.008) * 8                # 0..8

    # Volume de posts trouvés (signe de tendance active)
    volume_boost = _clamp(posts_count / 10.0) * 7            # 0..7

    tiktok_total = int(round(reach + engagement + virality + volume_boost))
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
