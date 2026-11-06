"""Connecteur Meta Ads Library via SerpApi."""
from __future__ import annotations

from typing import Any, Dict, List

from .serpapi_client import serpapi_get


def fetch_meta_ads(
    query: str,
    country: str = "FR",
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Cherche des publicités actives sur la Meta Ads Library.
    Retourne les annonces enrichies avec signaux e-commerce.
    """
    try:
        data = serpapi_get(
            engine="facebook_ads_library",
            params={
                "q": query,
                "country": country,
                "ad_type": "ALL",
                "ad_active_status": "ACTIVE",
            },
        )
    except RuntimeError as e:
        # 400 = engine non disponible sur ce plan SerpApi → on skip silencieusement
        if "400" in str(e):
            return []
        print(f"[meta_ads] erreur pour '{query}': {e}")
        return []
    except Exception as e:
        print(f"[meta_ads] erreur pour '{query}': {e}")
        return []

    raw_ads = data.get("ads_archive", []) or data.get("organic_results", []) or []
    ads = []

    for ad in raw_ads[:max_results]:
        # Détection e-commerce : lien vers boutique / bouton d'achat
        cta = (ad.get("cta_type", "") or "").upper()
        is_ecommerce = cta in {"SHOP_NOW", "BUY_NOW", "ORDER_NOW", "GET_OFFER", "LEARN_MORE"}

        body_text = ad.get("body", {}) or {}
        if isinstance(body_text, dict):
            text = body_text.get("text", "")
        else:
            text = str(body_text)

        ads.append({
            "ad_id": ad.get("id", ""),
            "page_name": ad.get("page_name", ""),
            "cta": cta,
            "is_ecommerce": is_ecommerce,
            "text": text[:300],
            "start_date": ad.get("ad_creation_time", ""),
            "image_url": (ad.get("snapshot", {}) or {}).get("images", [None])[0],
        })

    return ads


def meta_ads_signal(ads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transforme la liste d'annonces en signal de validation publicitaire.
    """
    if not ads:
        return {"ad_validation_score": 0, "active_ads": 0, "ecommerce_ads": 0}

    ecom_ads = [a for a in ads if a.get("is_ecommerce")]
    unique_advertisers = len(set(a["page_name"] for a in ads if a.get("page_name")))

    # Score 0..100 : plus il y a d'annonceurs e-commerce actifs, plus c'est un signal fort
    advertiser_score = min(unique_advertisers / 5.0, 1.0) * 50   # 5 annonceurs = max
    volume_score = min(len(ecom_ads) / 10.0, 1.0) * 30           # 10 annonces e-com = max
    diversity_score = min(unique_advertisers / 3.0, 1.0) * 20    # 3 annonceurs uniques = max

    validation_score = int(round(advertiser_score + volume_score + diversity_score))

    return {
        "ad_validation_score": min(validation_score, 100),
        "active_ads": len(ads),
        "ecommerce_ads": len(ecom_ads),
        "unique_advertisers": unique_advertisers,
        "sample_ads": ads[:3],
    }
