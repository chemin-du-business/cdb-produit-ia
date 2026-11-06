"""Connecteur TikTok Discover (trending hashtags/sounds) via SerpApi."""
from __future__ import annotations

from typing import Any, Dict, List

from .serpapi_client import serpapi_get


def fetch_tiktok_trending(
    query: str = "",
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Récupère les contenus trending TikTok liés à une requête.
    Retourne les posts avec vues, likes et signaux viraux.
    """
    try:
        params: Dict[str, Any] = {"max_results": max_results}
        if query:
            params["q"] = query

        data = serpapi_get(
            engine="tiktok",
            params=params,
        )
    except Exception as e:
        print(f"[tiktok_discover] erreur pour '{query}': {e}")
        return []

    raw = data.get("organic_results", []) or data.get("video_results", []) or []
    posts = []

    for item in raw[:max_results]:
        stats = item.get("stats", {}) or {}
        views = _safe_int(stats.get("play_count") or stats.get("views") or item.get("views"))
        likes = _safe_int(stats.get("digg_count") or stats.get("likes") or item.get("likes"))
        shares = _safe_int(stats.get("share_count") or stats.get("shares") or item.get("shares"))
        comments = _safe_int(stats.get("comment_count") or stats.get("comments") or item.get("comments"))

        posts.append({
            "title": item.get("title", "") or item.get("desc", ""),
            "author": (item.get("author", {}) or {}).get("unique_id", ""),
            "views": views,
            "likes": likes,
            "shares": shares,
            "comments": comments,
            "thumbnail": item.get("thumbnail", "") or item.get("cover", ""),
            "url": item.get("link", "") or item.get("url", ""),
            "created_at": item.get("create_time", ""),
            "hashtags": [t.lstrip("#") for t in (item.get("text_extra", []) or []) if str(t).startswith("#")],
        })

    return posts


def tiktok_discover_signal(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transforme les posts trending en signal de viralité TikTok.
    """
    if not posts:
        return {"viral_score": 0, "total_views": 0, "avg_engagement_rate": 0}

    total_views = sum(p.get("views") or 0 for p in posts)
    total_likes = sum(p.get("likes") or 0 for p in posts)
    total_shares = sum(p.get("shares") or 0 for p in posts)

    engagement_rates = []
    for p in posts:
        v = p.get("views") or 0
        if v > 0:
            rate = ((p.get("likes") or 0) + (p.get("shares") or 0) + (p.get("comments") or 0)) / v
            engagement_rates.append(rate)

    avg_engagement = round(sum(engagement_rates) / len(engagement_rates), 4) if engagement_rates else 0

    # Score viral 0..100
    view_score = min(total_views / 5_000_000.0, 1.0) * 50   # 5M vues = max
    engagement_score = min(avg_engagement / 0.08, 1.0) * 30  # 8% engagement = max
    volume_score = min(len(posts) / 10.0, 1.0) * 20

    viral_score = int(round(view_score + engagement_score + volume_score))

    return {
        "viral_score": min(viral_score, 100),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_shares": total_shares,
        "avg_engagement_rate": avg_engagement,
        "posts_count": len(posts),
        "top_posts": posts[:3],
    }


def _safe_int(x: Any) -> int:
    try:
        return int(str(x).replace(",", "").replace(" ", "").strip())
    except Exception:
        return 0
