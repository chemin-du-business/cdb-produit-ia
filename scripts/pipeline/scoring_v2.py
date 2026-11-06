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
    amz_results = int(amz.get("results_count") or 0)
    amz_reviews = int(amz.get("total_reviews") or 0)
    amz_bestseller = bool(amz.get("has_bestseller") or amz.get("has_bestseller_badge"))
    amz_choice = bool(amz.get("has_amazon_choice"))
    # Plancher : si présence sur Amazon → au moins 12 pts
    if amz_results > 0:
        amz_base = 12
        amz_review_pts = _clamp(amz_reviews / 60.0) * 13   # 60 avis = +13 pts
        amz_badge_pts = 10 if amz_bestseller else (5 if amz_choice else 0)
        amazon_score = int(round(amz_base + amz_review_pts + amz_badge_pts))
    else:
        amazon_score = 0

    # ── Google Trends (30 pts) ──────────────────────────────────────────────
    trends = signals.get("google_trends") or {}
    trends_raw = int(trends.get("current_value") or 0)
    trends_direction = trends.get("trend_direction", "unknown")
    dir_mult = {"rising": 1.0, "stable": 0.85, "declining": 0.5, "unknown": 0.75}
    if trends_raw > 0:
        trends_score = int(round(_clamp(trends_raw / 100.0) * dir_mult.get(trends_direction, 0.75) * 30))
        trends_score = max(trends_score, 8)   # plancher 8 si Trends répond
    else:
        trends_score = 0

    # ── Google Shopping (20 pts) ────────────────────────────────────────────
    shopping = signals.get("google_shopping") or {}
    shop_results = int(shopping.get("results_count") or 0)
    shop_reviews = int(shopping.get("total_reviews") or 0)
    if shop_results > 0:
        shop_base = 8
        shop_review_pts = _clamp(shop_reviews / 100.0) * 8   # 100 avis = +8 pts
        shop_volume_pts = _clamp(shop_results / 5.0) * 4     # 5 résultats = +4 pts
        shopping_score = int(round(shop_base + shop_review_pts + shop_volume_pts))
    else:
        shopping_score = 0

    google_score = trends_score + shopping_score

    # ── TikTok Shop (15 pts) ────────────────────────────────────────────────
    tshop = signals.get("tiktok_shop") or {}
    tshop_results = int(tshop.get("results_count") or 0)
    tshop_sales = int(tshop.get("total_sales") or 0)
    if tshop_results > 0:
        tshop_base = 5
        tshop_sales_pts = _clamp(tshop_sales / 100.0) * 10  # 100 ventes = +10 pts
        tshop_score = int(round(tshop_base + tshop_sales_pts))
    else:
        tshop_score = 0

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
