from __future__ import annotations

import os
from datetime import date
from typing import Any, Dict, List
from slugify import slugify

from scripts.connectors.tiktok_creative_center import fetch_tiktok_creative_center_candidates
from scripts.connectors.pinterest_official import fetch_pinterest_signal

from scripts.pipeline.merge import merge_candidates
from scripts.pipeline.scoring import score_candidate
from scripts.pipeline.diversity import apply_category_diversity
from scripts.pipeline.ai import is_sellable_product, generate_analysis
from scripts.pipeline.supabase_db import get_supabase, upsert_products, set_current_run_date, insert_run_log
from scripts.pipeline.utils import utc_now_iso


TOP_N = int(os.environ.get("TOP_N", "20"))
MAX_PER_CATEGORY = int(os.environ.get("MAX_PER_CATEGORY", "3"))
REGION = os.environ.get("RUN_REGION", "FR")


BAD_TERMS = [
    "mots fléchés",
    "mots croisés",
    "synonyme",
    "solution",
    "définition",
    "definition",
    "3 lettres",
    "4 lettres",
    "5 lettres",
    "review",
    "reviews",
    "best ",
    "top ",
    "comparatif",
    "compare",
    "vs",
]

GENERIC_TERMS = ["accessoire", "produit", "objet", "article", "outil"]


def is_bad_title(title: str) -> bool:
    t = (title or "").strip().lower()
    if not t:
        return True
    if any(x in t for x in BAD_TERMS):
        return True
    if any(x in t for x in GENERIC_TERMS) and len(t.split()) <= 3:
        return True
    if len(t.split()) <= 2:
        return True
    return False


def infer_category(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["visage", "peau", "skincare", "brosse", "serum", "crème", "beaut"]):
        return "beauté"
    if any(k in t for k in ["lampe", "led", "veilleuse", "projecteur", "déco", "deco", "maison"]):
        return "maison"
    if any(k in t for k in ["sport", "fitness", "muscu", "running", "shaker", "gourde"]):
        return "fitness"
    if any(k in t for k in ["cuisine", "air fryer", "poêle", "poele", "mixeur", "couteau"]):
        return "cuisine"
    if any(k in t for k in ["bébé", "bebe", "enfant", "maman"]):
        return "bébé"
    if any(k in t for k in ["chien", "chat", "animaux", "litière", "litiere", "laisse"]):
        return "animaux"
    if any(k in t for k in ["voiture", "auto", "moto"]):
        return "auto"
    return "autre"


def main() -> None:
    sb = get_supabase()
    run_date = str(date.today())

    stats: Dict[str, Any] = {"run_date": run_date, "region": REGION}
    errors: Dict[str, Any] = {}

    try:
        raw = fetch_tiktok_creative_center_candidates(region=REGION, limit=140)
        stats["candidates_raw"] = len(raw)

        merged = merge_candidates(raw)
        stats["candidates_merged"] = len(merged)

        sellable: List[Dict[str, Any]] = []
        for c in merged:
            title = c.get("title") or ""
            if is_bad_title(title):
                continue
            if not is_sellable_product(title, geo=REGION):
                continue
            sellable.append(c)

        stats["candidates_sellable"] = len(sellable)

        enriched: List[Dict[str, Any]] = []
        for c in sellable:
            title = c["title"]
            c["category"] = c.get("category") or infer_category(title)
            c["tags"] = c.get("tags") or [w for w in slugify(title).split("-")[:4] if w]
            c.setdefault("signals", {})

            pin = fetch_pinterest_signal(title)
            c["signals"]["pinterest"] = pin

            pin_hits = int(pin.get("hits", 0) or 0)
            if pin_hits > 0:
                if "pinterest" not in c["sources"]:
                    c["sources"].append("pinterest")
                if pin.get("image_url") and not c.get("image_url"):
                    c["image_url"] = pin["image_url"]
                    c["image_source"] = "pinterest"
                    c["source_url"] = pin.get("source_url")

            enriched.append(c)

        stats["candidates_enriched"] = len(enriched)

        for c in enriched:
            s = score_candidate(c)
            c["score"] = s["score"]
            c["score_breakdown"] = s["score_breakdown"]

        enriched.sort(key=lambda x: x["score"], reverse=True)

        diversified = apply_category_diversity(enriched, max_per_category=MAX_PER_CATEGORY)

        winners = diversified[:TOP_N]
        stats["topN"] = len(winners)

        rows: List[Dict[str, Any]] = []
        for w in winners:
            title = w["title"]
            slug = slugify(title)[:80]

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

            summary = ""
            try:
                summary = (analysis.get("positioning", {}) or {}).get("main_promise", "") or ""
            except Exception:
                summary = ""

            rows.append(
                {
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
                    "image_url": w.get("image_url"),
                    "image_source": w.get("image_source"),
                    "source_url": w.get("source_url"),
                    "is_hidden": False,
                    "published_at": utc_now_iso(),
                }
            )

        upsert_products(sb, rows)
        set_current_run_date(sb, run_date)
        insert_run_log(sb, run_date, "success", stats, errors)

        print("OK ✅", stats)

    except Exception as e:
        errors["fatal"] = str(e)
        insert_run_log(sb, run_date, "fail", stats, errors)
        raise


if __name__ == "__main__":
    main()
