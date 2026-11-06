"""Pipeline V4 — 100% SerpApi, sans Apify."""
from __future__ import annotations

import os
from datetime import date
from typing import Dict, List, Set

from slugify import slugify

# Connecteurs SerpApi
from scripts.connectors.tiktok_discover import fetch_tiktok_trending, tiktok_discover_signal
from scripts.connectors.tiktok_shop import fetch_tiktok_shop_products, tiktok_shop_signal
from scripts.connectors.amazon_products import fetch_amazon_products, amazon_product_demand_signal
from scripts.connectors.google_trends import fetch_google_trends
from scripts.connectors.google_shopping import fetch_google_shopping, google_shopping_signal
from scripts.connectors.meta_ads import fetch_meta_ads, meta_ads_signal
from scripts.connectors.youtube_videos import fetch_youtube_video, youtube_embed_url

# Pipeline
from scripts.pipeline.scoring_v2 import score_candidate_v2
from scripts.pipeline.supabase_db import get_supabase, upsert_products
from scripts.pipeline.ai import extract_product_name, is_sellable_product, generate_analysis, _ensure_french_title
from scripts.weekly_run_v3 import infer_category, make_tags

TOP_N = int(os.environ.get("TOP_N", "20"))
REGION = os.environ.get("RUN_REGION", "FR")

# Mots-clés de découverte — catégories populaires dropshipping FR
# 6 mots-clés max pour limiter la conso SerpApi en discovery
DISCOVERY_KEYWORDS = [
    "gadget cuisine viral pas cher",
    "accessoire chien chat tendance",
    "gadget voiture organisateur",
    "lampe led chambre décoration",
    "accessoire bébé enfant pratique",
    "outil jardinage plantes maison",
]


def _short_keyword(title: str, max_words: int = 4) -> str:
    """Réduit un titre à max_words mots pour Google Trends (trop long = no results)."""
    words = title.strip().split()
    return " ".join(words[:max_words])


def discover_candidates_serpapi(geo: str = "FR") -> List[Dict]:
    """
    Découverte de produits 100% SerpApi.
    Sources : TikTok Shop + Amazon + Google Shopping sur des keywords de niche.
    Retourne une liste de candidats {title, sources, signals}.
    """
    seen: Set[str] = set()
    candidates: List[Dict] = []

    for kw in DISCOVERY_KEYWORDS:
        print(f"  🔎 Discovery keyword: {kw}")

        # ── TikTok Shop ──────────────────────────────────────────────────────
        try:
            tshop = fetch_tiktok_shop_products(kw, max_results=10)
            for p in tshop:
                name = (p.get("title") or "").strip()
                if name and name.lower() not in seen:
                    seen.add(name.lower())
                    candidates.append({
                        "raw_title": name,
                        "sources": ["tiktok_shop"],
                        "signals": {"tiktok_shop_discovery": {
                            "sales_count": p.get("sales_count", 0),
                            "rating": p.get("rating"),
                            "price_usd": p.get("price_usd"),
                        }},
                    })
        except Exception as e:
            print(f"    [tiktok_shop discovery] {e}")

        # ── Amazon ───────────────────────────────────────────────────────────
        try:
            amz = fetch_amazon_products(kw, geo=geo, max_results=10)
            for p in amz:
                name = (p.get("title") or "").strip()
                if name and name.lower() not in seen:
                    seen.add(name.lower())
                    candidates.append({
                        "raw_title": name,
                        "sources": ["amazon"],
                        "signals": {"amazon_discovery": {
                            "rating": p.get("rating"),
                            "reviews_count": p.get("reviews_count", 0),
                            "badge": p.get("badge", ""),
                        }},
                    })
        except Exception as e:
            print(f"    [amazon discovery] {e}")

        # ── Google Shopping ──────────────────────────────────────────────────
        try:
            shopping = fetch_google_shopping(kw, geo=geo, max_results=10)
            for p in shopping:
                name = (p.get("title") or "").strip()
                if name and name.lower() not in seen:
                    seen.add(name.lower())
                    candidates.append({
                        "raw_title": name,
                        "sources": ["google_shopping"],
                        "signals": {},
                    })
        except Exception as e:
            print(f"    [google_shopping discovery] {e}")

    print(f"  ✅ {len(candidates)} candidats bruts découverts")
    return candidates


def enrich_with_serpapi(title: str, geo: str = "FR") -> Dict:
    """
    Enrichissement complet SerpApi pour un produit validé.
    Retourne les signaux agrégés de toutes les sources.
    """
    signals: Dict = {}

    # Google Trends — keyword court (max 4 mots) pour éviter "no results"
    trends_results = fetch_google_trends([_short_keyword(title)], geo=geo)
    if trends_results:
        t = trends_results[0]
        signals["google_trends"] = {
            "current_value": t.get("current_value", 0),
            "peak_value": t.get("peak_value", 0),
            "trend_direction": t.get("trend_direction", "unknown"),
            "rising_queries": t.get("rising_queries", [])[:3],
            "timeline": t.get("timeline", []),
        }

    # Amazon
    amz_products = fetch_amazon_products(title, geo=geo)
    amz_signal = amazon_product_demand_signal(amz_products)
    # Traduire les titres des top produits en français
    for prod in (amz_signal.get("top_products") or [])[:3]:
        raw = prod.get("title", "")
        if raw:
            prod["title"] = _ensure_french_title(raw, geo=geo)
    signals["amazon"] = amz_signal
    if amz_products:
        signals["image_url"] = amz_products[0].get("image") or None
        signals["source_url"] = amz_products[0].get("url") or None

    # Google Shopping
    shopping_products = fetch_google_shopping(title, geo=geo)
    signals["google_shopping"] = google_shopping_signal(shopping_products)
    if not signals.get("image_url") and shopping_products:
        signals["image_url"] = shopping_products[0].get("thumbnail") or None

    # Meta Ads
    meta_ad_list = fetch_meta_ads(title, country=geo)
    signals["meta_ads"] = meta_ads_signal(meta_ad_list)

    # TikTok Shop
    tshop_products = fetch_tiktok_shop_products(title)
    signals["tiktok_shop"] = tiktok_shop_signal(tshop_products)
    if not signals.get("image_url") and tshop_products:
        signals["image_url"] = tshop_products[0].get("thumbnail") or None

    # TikTok Discover — tentative (retourne 400 si engine non dispo sur le plan)
    discover_posts = fetch_tiktok_trending(query=title)
    if discover_posts:
        signals["tiktok_discover"] = tiktok_discover_signal(discover_posts)
        if not signals.get("source_url"):
            signals["source_url"] = discover_posts[0].get("url") or None
        if not signals.get("image_url"):
            signals["image_url"] = discover_posts[0].get("thumbnail") or None

    # Image fallback : TikTok Shop thumbnail (souvent de bonne qualité)
    if not signals.get("image_url") and tshop_products:
        signals["image_url"] = tshop_products[0].get("thumbnail") or None

    # YouTube — vidéo de démonstration produit (1 crédit SerpApi)
    yt_url = fetch_youtube_video(title)
    if yt_url:
        signals["youtube_url"] = yt_url

    return signals


def main() -> None:
    sb = get_supabase()
    run_date = str(date.today())

    # ── Étape 1 : Découverte SerpApi multi-sources ───────────────────────────
    print("🔍 Découverte de produits via SerpApi...")
    raw_candidates = discover_candidates_serpapi(geo=REGION)

    # ── Étape 2 : Filtrage IA (nom produit + vendabilité) ───────────────────
    print(f"🤖 Filtrage IA de {len(raw_candidates)} candidats bruts...")
    sellable: List[dict] = []
    seen_products: Set[str] = set()

    for c in raw_candidates:
        raw_title = c.get("raw_title", "")
        product = extract_product_name(raw_title, geo=REGION)
        if not product:
            continue
        if not is_sellable_product(product, geo=REGION):
            continue
        key = product.lower().strip()
        if key in seen_products:
            continue
        seen_products.add(key)
        c["title"] = product
        sellable.append(c)

    print(f"  ✅ {len(sellable)} produits vendables retenus")

    # ── Étape 3 : Pré-sélection top 40 (score discovery brut) ───────────────
    # Score basé sur les signaux de découverte disponibles
    for c in sellable:
        disc_sig = c.get("signals", {})
        tshop_sales = disc_sig.get("tiktok_shop_discovery", {}).get("sales_count", 0) or 0
        amz_reviews = disc_sig.get("amazon_discovery", {}).get("reviews_count", 0) or 0
        is_badge = bool(disc_sig.get("amazon_discovery", {}).get("badge"))
        c["_discovery_score"] = min(tshop_sales / 100, 50) + min(amz_reviews / 50, 30) + (20 if is_badge else 0)

    sellable.sort(key=lambda x: x.get("_discovery_score", 0), reverse=True)
    candidates_to_enrich = sellable[:8]

    # ── Étape 4 : Enrichissement SerpApi complet ─────────────────────────────
    print(f"🔍 Enrichissement SerpApi de {len(candidates_to_enrich)} candidats...")
    for c in candidates_to_enrich:
        title = c["title"]
        print(f"  → {title}")
        serpapi_signals = enrich_with_serpapi(title, geo=REGION)
        c.setdefault("signals", {})
        # Conserver l'image/source_url récupérée pendant l'enrichissement
        c["_image_url"] = serpapi_signals.pop("image_url", None)
        c["_source_url"] = serpapi_signals.pop("source_url", None)
        c["_youtube_url"] = serpapi_signals.pop("youtube_url", None)
        c["signals"].update(serpapi_signals)

    # ── Étape 5 : Score V2 multi-sources ────────────────────────────────────
    for c in candidates_to_enrich:
        result = score_candidate_v2(c)
        c["score"] = result["score"]
        c["score_breakdown"] = result["score_breakdown"]
        c["status"] = result["status"]
        c["category"] = infer_category(c["title"])
        c["tags"] = make_tags(c["title"])

    candidates_to_enrich.sort(key=lambda x: x.get("score", 0), reverse=True)
    winners = candidates_to_enrich[:TOP_N]

    # ── Étape 6 : Génération analyse IA ─────────────────────────────────────
    rows: List[Dict] = []
    for w in winners:
        title = w["title"]
        category = w.get("category", "autre")
        tags = w.get("tags", [])

        analysis = generate_analysis(
            {
                "title": title,
                "category": category,
                "tags": tags,
                "sources": w.get("sources", []),
                "signals": w.get("signals", {}),
            },
            geo=REGION,
        )

        summary = (analysis.get("positioning", {}) or {}).get("main_promise", "") or ""

        rows.append({
            "run_date": run_date,
            "title": title,
            "slug": slugify(title)[:80],
            "category": category,
            "tags": tags,
            "sources": w.get("sources", []),
            "score": int(w.get("score", 0)),
            "score_breakdown": w.get("score_breakdown", {}),
            "status": w.get("status", "Émergent"),
            "summary": summary,
            "signals": w.get("signals", {}),
            "analysis": analysis,
            "image_url": w.get("_image_url"),
            "image_source": None,
            "source_url": w.get("_source_url") or w.get("_youtube_url"),
            "video_storage_url": None,
            "is_hidden": False,
        })

    upsert_products(sb, rows)

    print("✅ Pipeline V4 terminé", {
        "run_date": run_date,
        "region": REGION,
        "candidates_raw": len(raw_candidates),
        "candidates_sellable": len(sellable),
        "candidates_enriched": len(candidates_to_enrich),
        "topN": len(winners),
    })


if __name__ == "__main__":
    main()
