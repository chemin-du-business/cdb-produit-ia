"""Connecteur Amazon via SerpApi (amazon_search engine)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .serpapi_client import serpapi_get

_DOMAIN_MAP = {"FR": "amazon.fr", "US": "amazon.com", "DE": "amazon.de"}


def fetch_amazon_products(
    query: str,
    geo: str = "FR",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Cherche un produit sur Amazon et retourne les résultats enrichis.
    """
    domain = _DOMAIN_MAP.get(geo.upper(), "amazon.fr")

    try:
        data = serpapi_get(
            engine="amazon",
            params={
                "amazon_domain": domain,
                "k": query,
                "s": "review-rank",  # tri par avis = best-sellers
            },
        )
    except Exception as e:
        print(f"[amazon] erreur pour '{query}' ({domain}): {e}")
        return []

    raw_results = data.get("organic_results", [])
    products = []

    for item in raw_results[:max_results]:
        rating = _safe_float(item.get("rating"))
        reviews = _safe_int(item.get("reviews"))
        price_raw = item.get("price", {}) or {}

        price_value: Optional[float] = None
        if isinstance(price_raw, dict):
            price_value = _safe_float(price_raw.get("value") or price_raw.get("raw", "").replace("€", "").replace(",", ".").strip())
        elif isinstance(price_raw, (int, float, str)):
            price_value = _safe_float(str(price_raw).replace("€", "").replace(",", ".").strip())

        products.append({
            "title": item.get("title", ""),
            "asin": item.get("asin", ""),
            "price": price_value,
            "currency": "EUR" if geo == "FR" else "USD",
            "rating": rating,
            "reviews_count": reviews,
            "image": item.get("thumbnail", ""),
            "url": item.get("link", ""),
            "is_prime": bool(item.get("is_prime", False)),
            "badge": item.get("badge", ""),  # "Best Seller", "Amazon's Choice", etc.
            "domain": domain,
        })

    return products


def amazon_product_demand_signal(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agrège les résultats Amazon en signal de demande.
    """
    if not products:
        return {"demand_score": 0, "avg_price": None, "total_reviews": 0, "has_bestseller": False}

    prices = [p["price"] for p in products if p.get("price")]
    avg_price = round(sum(prices) / len(prices), 2) if prices else None
    total_reviews = sum(p.get("reviews_count", 0) or 0 for p in products)
    has_bestseller = any("best seller" in (p.get("badge", "") or "").lower() for p in products)
    has_choice = any("choice" in (p.get("badge", "") or "").lower() for p in products)

    # Score de demande 0..100 — calibré dropshipping (produits récents, peu d'avis)
    review_score = min(total_reviews / 80.0, 1.0) * 50   # 80 avis = max (était 500)
    bestseller_bonus = 30 if has_bestseller else (15 if has_choice else 0)
    count_bonus = min(len(products) / 5.0, 1.0) * 20     # 5 résultats = max (était 10)

    demand_score = int(round(review_score + bestseller_bonus + count_bonus))

    return {
        "demand_score": min(demand_score, 100),
        "avg_price": avg_price,
        "total_reviews": total_reviews,
        "has_bestseller": has_bestseller,
        "has_amazon_choice": has_choice,
        "results_count": len(products),
        "top_products": products[:3],
    }


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
