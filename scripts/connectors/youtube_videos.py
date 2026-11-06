"""Connecteur YouTube via SerpApi — récupère une vidéo de démonstration produit."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .serpapi_client import serpapi_get


def fetch_youtube_video(query: str, max_results: int = 5) -> Optional[str]:
    """
    Cherche une vidéo YouTube de démonstration pour un produit.
    Retourne l'URL YouTube de la meilleure vidéo ou None.
    """
    try:
        data = serpapi_get(
            engine="youtube",
            params={
                "search_query": f"{query} review démonstration",
                "num": max_results,
            },
        )
    except RuntimeError as e:
        if "400" in str(e):
            return None
        print(f"[youtube] erreur pour '{query}': {e}")
        return None
    except Exception as e:
        print(f"[youtube] erreur pour '{query}': {e}")
        return None

    results = data.get("video_results", []) or []
    for item in results[:max_results]:
        link = item.get("link", "") or ""
        # Privilégier vidéos courtes (< 10 min) et non-chaînes de marque
        if "watch?v=" in link:
            return link

    return None


def youtube_embed_url(watch_url: str) -> Optional[str]:
    """Convertit une URL youtube.com/watch?v=X en URL d'embed."""
    if not watch_url:
        return None
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(watch_url)
        vid = parse_qs(parsed.query).get("v", [None])[0]
        if vid:
            return f"https://www.youtube.com/embed/{vid}?autoplay=0&rel=0"
    except Exception:
        pass
    return None
