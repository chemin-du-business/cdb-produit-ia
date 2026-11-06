"""Pipeline V4 — multi-sources SerpApi + Apify TikTok."""
from __future__ import annotations

import os
from datetime import date
from typing import Dict, List

from slugify import slugify

# Connecteurs
from scripts.connectors.tiktok_hashtag_apify import fetch_tiktok_candidates_from_hashtags
from scripts.connectors.tiktok_discover import fetch_tiktok_trending, tiktok_discover_signal
from scripts.connectors.tiktok_shop import fetch_tiktok_shop_products, tiktok_shop_signal
from scripts.connectors.amazon_products import fetch_amazon_products, amazon_product_demand_signal
from scripts.connectors.google_trends import fetch_google_trends
from scripts.connectors.google_shopping import fetch_google_shopping, google_shopping_signal
from scripts.connectors.meta_ads import fetch_meta_ads, meta_ads_signal

# Pipeline
from scripts.pipeline.merge import merge_candidates
from scripts.pipeline.scoring_v2 import score_candidate_v2
from scripts.pipeline.supabase_db import get_supabase, upsert_products
from scripts.pipeline.ai import extract_product_name, is_sellable_product, generate_analysis
from scripts.weekly_run_v3 import infer_category, make_tags

TOP_N = int(os.environ.get("TOP_N", "20"))
REGION = os.environ.get("RUN_REGION", "FR")


def enrich_with_serpapi(title: str, geo: str = "FR") -> Dict:
    """
    Lance les 5 connecteurs SerpApi en séquentiel pour un produit.
    Retourne un dict de signaux agrégés.
    """
    signals: Dict = {}

    # Google Trends
    trends_results = fetch_google_trends([title], geo=geo)
    if trends_results:
        t = trends_results[0]
        signals["google_trends"] = {
            "current_value": t.get("current_value", 0),
            "peak_value": t.get("peak_value", 0),
            "trend_direction": t.get("trend_direction", "unknown"),
            "rising_queries": t.get("rising_queries", [])[:3],
        }

    # Amazon
    amz_products = fetch_amazon_products(title, geo=geo)
    signals["amazon"] = amazon_product_demand_signal(amz_products)

    # Google Shopping
    shopping_products = fetch_google_shopping(title, geo=geo)
    signals["google_shopping"] = google_shopping_signal(shopping_products)

    # Meta Ads
    meta_ad_list = fetch_meta_ads(title, country=geo)
    signals["meta_ads"] = meta_ads_signal(meta_ad_list)

    # TikTok Shop (US uniquement)
    tshop_products = fetch_tiktok_shop_products(title)
    signals["tiktok_shop"] = tiktok_shop_signal(tshop_products)

    # TikTok Discover
    discover_posts = fetch_tiktok_trending(query=title)
    signals["tiktok_discover"] = tiktok_discover_signal(discover_posts)

    return signals


def main() -> None:
    sb = get_supabase()
    run_date = str(date.today())

    # ── Étape 1 : TikTok Apify (source principale) ──────────────────────────
    raw = fetch_tiktok_candidates_from_hashtags()
    merged = merge_candidates(raw)

    # ── Étape 2 : Filtrage IA (nom produit + vendabilité) ───────────────────
    sellable: List[dict] = []
    for c in merged:
        caption = c.get("title", "")
        product = extract_product_name(caption, geo=REGION)
        if not product:
            continue
        if not is_sellable_product(product, geo=REGION):
            continue
        c["title"] = product
        sellable.append(c)

    # ── Étape 3 : Score TikTok-only pour pré-sélection top 40 ───────────────
    max_views = max([int((x.get("signals", {}).get("tiktok_hashtag", {}).get("views", 0) or 0)) for x in sellable] + [1])
    max_likes = max([int((x.get("signals", {}).get("tiktok_hashtag", {}).get("likes", 0) or 0)) for x in sellable] + [1])
    max_shares = max([int((x.get("signals", {}).get("tiktok_hashtag", {}).get("shares", 0) or 0)) for x in sellable] + [1])

    for c in sellable:
        from scripts.pipeline.scoring import score_candidate
        s = score_candidate(c, max_views=max_views, max_likes=max_likes, max_shares=max_shares)
        c["_tiktok_score"] = s["score"]

    sellable.sort(key=lambda x: x.get("_tiktok_score", 0), reverse=True)
    # On enrichit les 40 meilleurs (économise les crédits SerpApi)
    candidates_to_enrich = sellable[:40]

    # ── Étape 4 : Enrichissement SerpApi multi-sources ──────────────────────
    print(f"🔍 Enrichissement SerpApi de {len(candidates_to_enrich)} candidats...")
    for c in candidates_to_enrich:
        title = c["title"]
        print(f"  → {title}")
        serpapi_signals = enrich_with_serpapi(title, geo=REGION)
        # Merge avec les signaux TikTok existants
        c.setdefault("signals", {})
        c["signals"].update(serpapi_signals)

    # ── Étape 5 : Score V2 multi-sources ────────────────────────────────────
    for c in candidates_to_enrich:
        result = score_candidate_v2(
            c,
            max_views=max_views,
            max_likes=max_likes,
            max_shares=max_shares,
        )
        c["score"] = result["score"]
        c["score_breakdown"] = result["score_breakdown"]
        c["status"] = result["status"]

        title = c["title"]
        c["category"] = infer_category(title)
        c["tags"] = make_tags(title)

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
            "image_url": None,
            "image_source": None,
            "source_url": (w.get("signals", {}).get("tiktok_hashtag", {}) or {}).get("video_url"),
            "video_storage_url": (w.get("signals", {}).get("tiktok_hashtag", {}) or {}).get("video_storage_url"),
            "is_hidden": False,
        })

    upsert_products(sb, rows)

    print("✅ Pipeline V4 terminé", {
        "run_date": run_date,
        "region": REGION,
        "candidates_raw": len(raw),
        "candidates_sellable": len(sellable),
        "candidates_enriched": len(candidates_to_enrich),
        "topN": len(winners),
    })


if __name__ == "__main__":
    main()
