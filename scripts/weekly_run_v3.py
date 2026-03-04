from __future__ import annotations

import os
from datetime import date
from typing import Any, Dict, List

from slugify import slugify

from scripts.connectors.tiktok_hashtag_apify import fetch_tiktok_candidates_from_hashtags
from scripts.pipeline.merge import merge_candidates
from scripts.pipeline.scoring import score_candidate
from scripts.pipeline.supabase_db import get_supabase, upsert_products
from scripts.pipeline.ai import extract_product_name, is_sellable_product, generate_analysis

TOP_N = int(os.environ.get("TOP_N", "20"))
REGION = os.environ.get("RUN_REGION", "FR")


def infer_category(title: str) -> str:
    t = (title or "").lower()
    if any(k in t for k in ["visage", "peau", "skincare", "brosse", "serum", "crème", "creme", "beaut"]):
        return "beauté"
    if any(k in t for k in ["lampe", "led", "veilleuse", "projecteur", "déco", "deco", "maison"]):
        return "maison"
    if any(k in t for k in ["sport", "fitness", "muscu", "running", "gourde", "shaker"]):
        return "fitness"
    if any(k in t for k in ["cuisine", "air fryer", "poêle", "poele", "mixeur", "couteau"]):
        return "cuisine"
    if any(k in t for k in ["bébé", "bebe", "enfant", "maman"]):
        return "bébé"
    if any(k in t for k in ["chien", "chat", "animaux", "litière", "litiere", "laisse"]):
        return "animaux"
    if any(k in t for k in ["voiture", "auto", "moto", "car"]):
        return "auto"
    return "autre"


def make_tags(title: str) -> List[str]:
    return [t for t in slugify(title).split("-")[:4] if t]


def main() -> None:
    sb = get_supabase()
    today = str(date.today())

    raw = fetch_tiktok_candidates_from_hashtags()
    merged = merge_candidates(raw)

    # 1) Extraction produit + filtre vendable
    sellable: List[Dict[str, Any]] = []
    for c in merged:
        caption = c.get("title", "")  # ici c'est la caption brute
        product = extract_product_name(caption, geo=REGION)
        if not product:
            continue

        if not is_sellable_product(product, geo=REGION):
            continue

        c["title"] = product
        sellable.append(c)

    # 2) Enrich minimal (category/tags) + source_url TikTok
    enriched: List[Dict[str, Any]] = []
    for c in sellable:
        title = c["title"]
        c["category"] = infer_category(title)
        c["tags"] = make_tags(title)
        c.setdefault("signals", {})

        # URL vidéo TikTok (toujours)
        video_url = (c.get("signals", {}).get("tiktok_hashtag", {}) or {}).get("video_url")
        if video_url:
            c["source_url"] = video_url

        enriched.append(c)

    # 3) Scoring
    # (on garde cette signature pour l'instant; on améliorera scoring.py ensuite)
    max_views = max(
        [int((x.get("signals", {}).get("tiktok_hashtag", {}).get("views", 0) or 0)) for x in enriched] + [1]
    )
    max_likes = max(
        [int((x.get("signals", {}).get("tiktok_hashtag", {}).get("likes", 0) or 0)) for x in enriched] + [1]
    )
    max_shares = max(
        [int((x.get("signals", {}).get("tiktok_hashtag", {}).get("shares", 0) or 0)) for x in enriched] + [1]
    )

    for c in enriched:
        s = score_candidate(c, max_views=max_views, max_likes=max_likes, max_shares=max_shares)
        c["score"] = s["score"]
        c["score_breakdown"] = s["score_breakdown"]

    enriched.sort(key=lambda x: x.get("score", 0), reverse=True)
    winners = enriched[:TOP_N]

    # 4) Analyse IA + rows Supabase
    rows: List[Dict[str, Any]] = []
    for w in winners:
        title = w["title"]

        analysis = generate_analysis(
            {
                "title": title,
                "category": w.get("category", "autre"),
                "tags": w.get("tags", []),
                "sources": w.get("sources", []),
                "signals": w.get("signals", {}),
            },
            geo=REGION,
        )

        rows.append(
            {
                "run_date": today,
                "title": title,
                "slug": slugify(title)[:80],
                "category": w.get("category", "autre"),
                "tags": w.get("tags", []),
                "sources": w.get("sources", []),
                "score": int(w.get("score", 0)),
                "score_breakdown": w.get("score_breakdown", {}),
                "summary": (analysis.get("positioning", {}) or {}).get("main_promise", "") or "",
                "signals": w.get("signals", {}),
                "analysis": analysis,
                "image_url": None,
                "image_source": None,
                "source_url": w.get("source_url") or (w.get("signals", {}).get("tiktok_hashtag", {}) or {}).get("video_url"),
                "is_hidden": False,
            }
        )

    upsert_products(sb, rows)

    print(
        "OK ✅",
        {
            "run_date": today,
            "region": REGION,
            "candidates_raw": len(raw),
            "candidates_merged": len(merged),
            "candidates_sellable": len(sellable),
            "candidates_enriched": len(enriched),
            "topN": len(winners),
        },
    )


if __name__ == "__main__":
    main()