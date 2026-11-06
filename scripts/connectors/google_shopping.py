"""Connecteur Google Shopping via SerpApi."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .serpapi_client import serpapi_get

_GL_MAP = {"FR": "fr", "US": "us", "DE": "de"}
_HL_MAP = {"FR": "fr", "US": "en", "DE": "de"}


def fetch_google_shopping(
    query: str,
    geo: str = "FR",
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Cherche un produit sur Google Shopping.
    Retourne les offres avec prix, vendeurs et positions.
    """
    gl = _GL_MAP.get(geo.upper(), "fr")
    hl = _HL_MAP.get(geo.upper(), "fr")

    try:
        data = serpapi_get(
            engine="google_shopping",
            params={
                "q": query,
                "gl": gl,
                "hl": hl,
                "num": max_results,
            },
        )
    except Exception as e:
        print(f"[google_shopping] erreur pour '{query}': {e}")
        return []

    raw = data.get("shopping_results", []) or []
    products = []

    for item in raw[:max_results]:
        price_raw = item.get("price", "")
        price_value: Optional[float] = _parse_price(price_raw)

        products.append({
            "title": item.get("title", ""),
            "price": price_value,
            "currency": "EUR" if geo == "FR" else "USD",
            "source": item.get("source", ""),  # nom du vendeur
            "rating": _safe_float(item.get("rating")),
            "reviews": _safe_int(item.get("reviews")),
            "thumbnail": item.get("thumbnail", ""),
            "link": item.get("link", ""),
            "position": item.get("position", 0),
            "badge": item.get("badge", ""),
        })

    return products


def google_shopping_signal(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agrège les résultats Shopping en signal de marché.
    """
    if not products:
        return {"market_score": 0, "avg_price": None, "sellers_count": 0, "competition_level": "unknown"}

    prices = [p["price"] for p in products if p.get("price") and p["price"] > 0]
    avg_price = round(sum(prices) / len(prices), 2) if prices else None
    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None

    unique_sellers = len(set(p["source"] for p in products if p.get("source")))
    total_reviews = sum(p.get("reviews") or 0 for p in products)

    # Niveau de concurrence
    if unique_sellers >= 10:
        competition = "high"
    elif unique_sellers >= 5:
        competition = "medium"
    else:
        competition = "low"

    # Score marché calibré dropshipping — présence = bon signal, pénalité concurrence allégée
    presence_score = min(len(products) / 5.0, 1.0) * 55   # 5 résultats = max (était 10)
    review_score = min(total_reviews / 150.0, 1.0) * 35   # 150 avis = max (était 1000)
    # Pénalité concurrence réduite : beaucoup de vendeurs = marché validé en dropshipping
    competition_factor = 0.85 if competition == "high" else (0.92 if competition == "medium" else 1.0)
    market_score = int(round((presence_score + review_score) * competition_factor))

    return {
        "market_score": min(market_score, 100),
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "sellers_count": unique_sellers,
        "results_count": len(products),
        "total_reviews": total_reviews,
        "competition_level": competition,
        "top_sellers": [p["source"] for p in products[:5] if p.get("source")],
    }


def _parse_price(raw: Any) -> Optional[float]:
    if not raw:
        return None
    try:
        cleaned = str(raw).replace("€", "").replace("$", "").replace("\xa0", "").replace(" ", "").replace(",", ".").strip()
        # gérer "12.99" ou "12,99"
        return float(cleaned.split("–")[0].split("-")[0].strip())
    except Exception:
        return None


def _safe_float(x: Any) -> Optional[float]:
    try:
        return float(str(x).replace(",", ".").strip())
    except Exception:
        return None


def _safe_int(x: Any) -> int:
    try:
        return int(str(x).replace(",", "").replace(" ", "").strip())
    except Exception:
        return 0
