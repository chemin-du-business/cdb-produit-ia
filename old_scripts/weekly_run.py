from __future__ import annotations

import os
from datetime import date
from typing import Any, Dict, List
from slugify import slugify

from scripts.connectors.google_trends import fetch_google_trends_candidates
from scripts.connectors.pinterest import fetch_pinterest_signal
from scripts.connectors.tiktok import fetch_tiktok_signal

from scripts.pipeline.merge import merge_candidates
from scripts.pipeline.scoring import compute_max_interest, score_candidate
from scripts.pipeline.diversity import apply_category_diversity
from scripts.pipeline.ai import classify_sellability, generate_analysis
from scripts.pipeline.supabase_db import (
    get_supabase,
    upsert_products,
    set_current_run,
    insert_run_log,
)
from scripts.pipeline.utils import utc_now_iso
from scripts.pipeline.images import download_image, upload_image_to_supabase


RUN_GEO = os.environ.get("RUN_GEO", "FR").strip() or "FR"
RUN_MODE = os.environ.get("RUN_MODE", "trending").strip() or "trending"

TOP_N = int(os.environ.get("TOP_N", "10"))
ENRICH_TOP_K = int(os.environ.get("ENRICH_TOP_K", "30"))
MAX_PER_CATEGORY = int(os.environ.get("MAX_PER_CATEGORY", "3"))
SELLABLE_MIN_SCORE = int(os.environ.get("SELLABLE_MIN_SCORE", "60"))
DOWNLOAD_IMAGES = os.environ.get("DOWNLOAD_IMAGES", "1") == "1"


def infer_category(title: str) -> str:
    t = (title or "").lower()
    if any(k in t for k in ["visage", "peau", "skincare", "brosse", "serum", "sérum", "creme", "crème", "beauté", "beaute"]):
        return "beauté"
    if any(k in t for k in ["lampe", "led", "veilleuse", "projecteur", "déco", "deco", "maison", "rangement", "organisateur"]):
        return "maison"
    if any(k in t for k in ["sport", "fitness", "muscu", "running", "yoga", "pilates"]):
        return "fitness"
    if any(k in t for k in ["cuisine", "airfryer", "air fryer", "poêle", "mixeur", "couteau", "planche"]):
        return "cuisine"
    if any(k in t for k in ["bébé", "bebe", "enfant", "maman", "grossesse"]):
        return "bébé"
    if any(k in t for k in ["chien", "chat", "animaux", "litière", "laisse", "harnais"]):
        return "animaux"
    if any(k in t for k in ["voiture", "auto", "moto"]):
        return "auto"
    return "autre"


def tags_from_title(title: str) -> List[str]:
    s = slugify(title)
    parts = [p for p in s.split("-") if p]
    return parts[:4] if parts else []


def main() -> None:
    sb = get_supabase()
    run_date = str(date.today())
    mode = RUN_MODE if RUN_MODE in ("trending", "evergreen") else "trending"

    stats: Dict[str, Any] = {"run_date": run_date, "geo": RUN_GEO, "mode": mode}
    errors: Dict[str, Any] = {}

    try:
        # 1) Collect candidates from Google Trends (current)
        raw = fetch_google_trends_candidates(geo=RUN_GEO, limit_trending=25)
        stats["candidates_raw"] = len(raw)

        # 2) Merge/dedup
        merged = merge_candidates(raw)
        stats["candidates_merged"] = len(merged)

        # 3) Filter sellable products (quick reject + IA sellability)
        sellable: List[Dict[str, Any]] = []
        rejected = 0

        for c in merged:
            title = c.get("title") or ""
            verdict = classify_sellability(title, geo=RUN_GEO)

            c.setdefault("signals", {})
            c["signals"]["sellability"] = verdict

            if verdict.get("sellable") and int(verdict.get("score", 0)) >= SELLABLE_MIN_SCORE:
                sellable.append(c)
            else:
                rejected += 1

        stats["candidates_sellable"] = len(sellable)
        stats["candidates_rejected"] = rejected
        stats["sellable_min_score"] = SELLABLE_MIN_SCORE

        if not sellable:
            # no results -> log partial and exit clean
            insert_run_log(sb, run_date, "partial", stats, {"warn": "no sellable candidates"})
            set_current_run(sb, run_date, mode)
            print("No sellable candidates; done.")
            return

        # 4) Category & tags
        for c in sellable:
            c["category"] = c.get("category") or infer_category(c["title"])
            c["tags"] = c.get("tags") or tags_from_title(c["title"])
            c.setdefault("sources", [])
            if "google_trends" not in c["sources"]:
                c["sources"].append("google_trends")

        # 5) Pre-score (GT only)
        max_interest_pre = compute_max_interest(sellable)
        stats["max_interest_pre"] = max_interest_pre

        for c in sellable:
            s = score_candidate(c, max_interest=max_interest_pre)
            c["score"] = s["score"]
            c["score_breakdown"] = s["score_breakdown"]

        sellable.sort(key=lambda x: x.get("score", 0), reverse=True)

        # 6) Enrich top K with Pinterest + TikTok
        to_enrich = sellable[:max(1, ENRICH_TOP_K)]
        stats["enrich_top_k"] = len(to_enrich)

        enriched: List[Dict[str, Any]] = []

        for c in to_enrich:
            title = c["title"]
            c.setdefault("signals", {})
            c.setdefault("sources", [])

            # Pinterest
            pin = fetch_pinterest_signal(title, limit=25)
            c["signals"]["pinterest"] = pin
            if int(pin.get("pin_count", 0)) > 0 and "pinterest" not in c["sources"]:
                c["sources"].append("pinterest")
            if pin.get("image_url"):
                c["image_url"] = pin.get("image_url")
                c["image_source"] = "pinterest"
                c["source_url"] = pin.get("source_url")

            # TikTok
            tk = fetch_tiktok_signal(title, results_limit=20, proxy_country_code="FR")
            c["signals"]["tiktok"] = tk
            if int(tk.get("video_count", 0)) > 0 and "tiktok" not in c["sources"]:
                c["sources"].append("tiktok")

            enriched.append(c)

        stats["candidates_enriched"] = len(enriched)

        # 7) Final scoring (GT + Pinterest + TikTok)
        max_interest = compute_max_interest(enriched)
        stats["max_interest"] = max_interest

        for c in enriched:
            s = score_candidate(c, max_interest=max_interest)
            c["score"] = s["score"]
            c["score_breakdown"] = s["score_breakdown"]

        enriched.sort(key=lambda x: x.get("score", 0), reverse=True)

        # 8) Diversity by category
        diversified = apply_category_diversity(enriched, max_per_category=MAX_PER_CATEGORY)
        stats["after_diversity"] = len(diversified)

        # 9) Select winners
        winners = diversified[:TOP_N]
        stats["topN"] = len(winners)

        rows: List[Dict[str, Any]] = []
        images_uploaded = 0

        for w in winners:
            title = w["title"]
            slug = slugify(title)[:80]

            final_image_url = w.get("image_url")
            final_image_source = w.get("image_source")
            final_source_url = w.get("source_url")

            # Download Pinterest image and upload to Supabase Storage for stable URL
            if DOWNLOAD_IMAGES and final_image_url and final_image_source == "pinterest":
                img_bytes, content_type = download_image(final_image_url)
                if img_bytes:
                    public_url = upload_image_to_supabase(
                        sb,
                        slug=slug,
                        image_bytes=img_bytes,
                        content_type=content_type or "image/jpeg",
                        source="pinterest",
                    )
                    if public_url:
                        final_image_url = public_url
                        images_uploaded += 1

            # IA analysis for UI blocks
            analysis = generate_analysis(
                {
                    "title": title,
                    "category": w.get("category", "autre"),
                    "tags": w.get("tags", []),
                    "score": int(w.get("score", 0)),
                    "score_breakdown": w.get("score_breakdown", {}),
                    "sources": w.get("sources", []),
                    "signals": w.get("signals", {}),
                },
                geo=RUN_GEO,
            )

            # Summary for cards (use main promise)
            summary = ""
            try:
                summary = (analysis.get("positioning", {}) or {}).get("main_promise", "") or ""
            except Exception:
                summary = ""

            rows.append(
                {
                    "mode": mode,  # ✅ you added mode in DB
                    "run_date": run_date,
                    "title": title,
                    "slug": slug,
                    "category": w.get("category", "autre"),
                    "tags": w.get("tags", []),
                    "sources": w.get("sources", []),
                    "score": int(w.get("score", 0)),
                    "score_breakdown": w.get("score_breakdown", {}),
                    "summary": summary,
                    "signals": w.get("signals", {}),
                    "analysis": analysis,
                    "image_url": final_image_url,
                    "image_source": final_image_source,
                    "source_url": final_source_url,
                    "is_hidden": False,
                    "published_at": utc_now_iso(),
                }
            )

        stats["images_uploaded"] = images_uploaded

        # 10) Write to DB
        upsert_products(sb, rows)
        set_current_run(sb, run_date, mode)
        insert_run_log(sb, run_date, "success", stats, errors)

        print("OK ✅", stats)

    except Exception as e:
        errors["fatal"] = str(e)
        insert_run_log(sb, run_date, "fail", stats, errors)
        raise


if __name__ == "__main__":
    main()