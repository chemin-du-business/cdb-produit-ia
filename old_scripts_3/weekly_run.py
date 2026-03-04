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
from scripts.pipeline.ai import is_sellable_product, generate_analysis
from scripts.pipeline.supabase_db import (
    get_supabase,
    upsert_products,
    set_current_run_date,
    insert_run_log,
)
from scripts.pipeline.utils import utc_now_iso


TOP_N = int(os.environ.get("TOP_N", "20"))
MAX_PER_CATEGORY = int(os.environ.get("MAX_PER_CATEGORY", "3"))
GEO = os.environ.get("RUN_GEO", "FR")

# V1 stable: si social=0 on veut quand même TOP_N produits
MIN_SOCIAL_WINNERS = int(os.environ.get("MIN_SOCIAL_WINNERS", "0"))
MAX_TRENDS_ONLY_FALLBACK = int(os.environ.get("MAX_TRENDS_ONLY_FALLBACK", str(TOP_N)))


BAD_TERMS = [
    "mots fléchés",
    "mots croisés",
    "synonyme",
    "solution",
    "3 lettres",
    "4 lettres",
    "5 lettres",
    "best ",
    "top ",
    "review",
    "reviews",
    "comparison",
    "compare",
    "vs",
    "guide",
    "how to",
    "comment",
    "avis",
    "test",
    "meilleur",
    "meilleurs",
    "comparatif",
]

GENERIC_TERMS = [
    "accessoire",
    "produit",
    "objet",
    "article",
    "outil",
]


def is_bad_title(title: str) -> bool:
    t = (title or "").lower().strip()
    if not t:
        return True

    if any(x in t for x in BAD_TERMS):
        return True

    # "accessoire de X" etc. trop générique si court
    if any(x in t for x in GENERIC_TERMS) and len(t.split()) <= 3:
        return True

    # trop court => pas assez spécifique
    if len(t.split()) <= 2:
        return True

    return False


def infer_category(title: str) -> str:
    t = title.lower()

    if any(k in t for k in ["visage", "peau", "skincare", "brosse", "serum", "crème", "creme", "beaut"]):
        return "beauté"

    if any(k in t for k in ["lampe", "led", "veilleuse", "projecteur", "déco", "deco", "maison"]):
        return "maison"

    if any(k in t for k in ["sport", "fitness", "muscu", "running", "gourde", "shaker"]):
        return "fitness"

    if any(k in t for k in ["cuisine", "air fryer", "poêle", "poele", "mixeur", "couteau", "blender"]):
        return "cuisine"

    if any(k in t for k in ["bébé", "bebe", "enfant", "maman"]):
        return "bébé"

    if any(k in t for k in ["chien", "chat", "animaux", "litière", "litiere", "laisse", "pet"]):
        return "animaux"

    if any(k in t for k in ["voiture", "auto", "moto", "car"]):
        return "auto"

    if any(k in t for k in ["bureau", "desk", "ordinateur", "pc", "clavier", "souris", "support pc"]):
        return "bureau"

    if any(k in t for k in ["jardin", "garden", "désherb", "desherb", "plant", "arros"]):
        return "jardin"

    return "autre"


def main() -> None:
    sb = get_supabase()
    run_date = str(date.today())

    stats: Dict[str, Any] = {"run_date": run_date, "geo": GEO}
    errors: Dict[str, Any] = {}

    try:
        # 1) Collect
        raw = fetch_google_trends_candidates(geo=GEO, limit_trending=40)
        stats["candidates_raw"] = len(raw)

        # 2) Merge
        merged = merge_candidates(raw)
        stats["candidates_merged"] = len(merged)

        # 3) Filter produits vendables (IA)
        sellable: List[Dict[str, Any]] = []
        for c in merged:
            title = c.get("title", "")
            if not title:
                continue

            if is_bad_title(title):
                continue

            if not is_sellable_product(title, geo=GEO):
                continue

            sellable.append(c)

        stats["candidates_sellable"] = len(sellable)

        # 4) Enrich social signals (bonus, pas bloquant)
        enriched_social: List[Dict[str, Any]] = []
        fallback_trends_only: List[Dict[str, Any]] = []

        for c in sellable:
            title = c["title"]

            c["category"] = c.get("category") or infer_category(title)
            c["tags"] = c.get("tags") or [w for w in slugify(title).split("-")[:4] if w]
            c.setdefault("signals", {})

            # Pinterest
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

            # TikTok
            tk = fetch_tiktok_signal(title)
            c["signals"]["tiktok"] = tk
            tk_hits = int(tk.get("hits", 0) or 0)
            tk_views = int(tk.get("views_estimate", 0) or 0)

            if tk_hits > 0 or tk_views > 0:
                if "tiktok" not in c["sources"]:
                    c["sources"].append("tiktok")

            has_social = (pin_hits > 0) or (tk_hits > 0) or (tk_views > 0)
            if has_social:
                enriched_social.append(c)
            else:
                fallback_trends_only.append(c)

        stats["candidates_enriched_social"] = len(enriched_social)
        stats["candidates_fallback_trends_only"] = len(fallback_trends_only)

        # 5) Scoring social d'abord
        for c in enriched_social:
            s = score_candidate(c, max_interest=compute_max_interest(enriched_social) if enriched_social else 100)
            c["score"] = s["score"]
            c["score_breakdown"] = s["score_breakdown"]

        enriched_social.sort(key=lambda x: x["score"], reverse=True)

        # Puis compléter avec trends-only jusqu'à TOP_N
        used_fallback = False
        pool: List[Dict[str, Any]] = list(enriched_social)

        if len(pool) < MIN_SOCIAL_WINNERS and fallback_trends_only:
            used_fallback = True

        if len(pool) < TOP_N and fallback_trends_only:
            used_fallback = True

            max_interest_fb = compute_max_interest(fallback_trends_only)
            for c in fallback_trends_only:
                s = score_candidate(c, max_interest=max_interest_fb)
                c["score"] = s["score"]
                c["score_breakdown"] = s["score_breakdown"]

            fallback_trends_only.sort(key=lambda x: x["score"], reverse=True)

            needed = min(MAX_TRENDS_ONLY_FALLBACK, TOP_N - len(pool))
            pool.extend(fallback_trends_only[:needed])

        stats["fallback_trends_used"] = used_fallback
        stats["final_scored_pool"] = len(pool)

        # 6) Diversité catégorie
        diversified = apply_category_diversity(pool, max_per_category=MAX_PER_CATEGORY)

        # fallback si diversité trop restrictive
        if len(diversified) < TOP_N:
            diversified = pool

        # 7) Top produits
        winners = diversified[:TOP_N]
        stats["topN"] = len(winners)

        # 8) Analyse IA + rows Supabase
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
                geo=GEO,
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