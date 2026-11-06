"""Connecteur TikTok Shop US via SerpApi (google_shopping sur tiktok shop)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .serpapi_client import serpapi_get


def fetch_tiktok_shop_products(
    query: str,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Cherche des produits sur TikTok Shop US via SerpApi.
    Retourne les produits avec ventes, prix et scores de popularité.
    """
    try:
        data = serpapi_get(
            engine="tiktok_shop",
            params={
                "q": query,
                "country_code": "US",
            },
        )
    except Exception as e:
        print(f"[tiktok_shop] erreur pour '{query}': {e}")
        return []

    raw = data.get("organic_results", []) or data.get("products", []) or []
    products = []

    for item in raw[:max_results]:
        price_raw = item.get("price", {}) or {}
        if isinstance(price_raw, dict):
            price = _safe_float(price_raw.get("value") or price_raw.get("extracted_value"))
        else:
            price = _safe_float(str(price_raw).replace("$", "").strip())

        sales_raw = item.get("sold", "") or item.get("sales", "") or ""
        sales = _parse_sales(str(sales_raw))

        rating = _safe_float(item.get("rating") or item.get("stars"))
        reviews = _safe_int(item.get("reviews") or item.get("ratings_total"))

        products.append({
            "title": item.get("title", ""),
            "price_usd": price,
            "sales_count": sales,
            "rating": rating,
            "reviews_count": reviews,
            "thumbnail": item.get("thumbnail", "") or item.get("image", ""),
            "url": item.get("link", "") or item.get("url", ""),
            "shop_name": item.get("shop_name", "") or item.get("seller", ""),
        })

    return products


def tiktok_shop_signal(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transforme les produits TikTok Shop en signal de tendance e-commerce.
    """
    if not products:
        return {"shop_score": 0, "avg_price_usd": None, "total_sales": 0}

    prices = [p["price_usd"] for p in products if p.get("price_usd")]
    avg_price = round(sum(prices) / len(prices), 2) if prices else None

    total_sales = sum(p.get("sales_count") or 0 for p in products)
    total_reviews = sum(p.get("reviews_count") or 0 for p in products)

    # Score 0..100 — calibré dropshipping (ventes réelles TikTok Shop, produits récents)
    sales_score = min(total_sales / 150.0, 1.0) * 55    # 150 ventes = max (était 1000)
    review_score = min(total_reviews / 80.0, 1.0) * 25  # 80 avis = max (était 500)
    volume_score = min(len(products) / 5.0, 1.0) * 20   # 5 résultats = max (était 10)

    shop_score = int(round(sales_score + review_score + volume_score))

    return {
        "shop_score": min(shop_score, 100),
        "avg_price_usd": avg_price,
        "total_sales": total_sales,
        "total_reviews": total_reviews,
        "results_count": len(products),
        "top_products": products[:3],
    }


def _parse_sales(raw: str) -> int:
    """Convertit '1.2k sold', '500+ sold', '1,234' en entier."""
    raw = raw.lower().replace("sold", "").replace("+", "").replace(",", "").strip()
    try:
        if "k" in raw:
            return int(float(raw.replace("k", "")) * 1000)
        if "m" in raw:
            return int(float(raw.replace("m", "")) * 1_000_000)
        return int(float(raw)) if raw else 0
    except Exception:
        return 0


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
