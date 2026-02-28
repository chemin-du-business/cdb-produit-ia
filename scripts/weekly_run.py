from __future__ import annotations

import os
from datetime import date
from typing import Any, Dict, List
from slugify import slugify

from scripts.connectors.google_trends import fetch_google_trends_candidates
from scripts.connectors.pinterest import fetch_pinterest_candidates
from scripts.connectors.tiktok import fetch_tiktok_candidates

from scripts.pipeline.scoring import score_candidate
from scripts.pipeline.ai import generate_analysis
from scripts.pipeline.supabase_db import (
    get_supabase,
    upsert_products,
    set_current_run_date,
    insert_run_log,
)
from scripts.pipeline.utils import utc_now_iso

TOP_N_DEFAULT = 20

def merge_candidates(cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge by normalized title (simple).
    Combines sources + signals.
    """
    merged: Dict[str, Dict[str, Any]] = {}
    for c in cands:
        title = c["title"].strip()
        key = title.lower()
        if key not in merged:
            merged[key] = {
                "title": title,
                "sources": [],
                "signals": {},
            }
        # merge sources
        for s in c.get("sources", []):
            if s not in merged[key]["sources"]:
                merged[key]["sources"].append(s)
        # merge signals
        for k, v in (c.get("signals") or {}).items():
            merged[key]["signals"][k] = v

        # optional: if connector provides an image
        if c.get("image_url") and not merged[key].get("image_url"):
            merged[key]["image_url"] = c["image_url"]
            merged[key]["image_source"] = c.get("image_source")
            merged[key]["source_url"] = c.get("source_url")

        if c.get("category") and not merged[key].get("category"):
            merged[key]["category"] = c["category"]

        if c.get("tags"):
            merged[key].setdefault("tags", [])
            for t in c["tags"]:
                if t not in merged[key]["tags"]:
                    merged[key]["tags"].append(t)

    return list(merged.values())

def main():
    geo = os.environ.get("RUN_GEO", "FR")
    run_date = str(date.today())  # weekly: you can set to "monday date" later
    topN = TOP_N_DEFAULT

    sb = get_supabase()

    stats: Dict[str, Any] = {"geo": geo, "run_date": run_date}
    errors: Dict[str, Any] = {}

    try:
        # 1) Collect
        trends = fetch_google_trends_candidates(geo=geo)
        pin = fetch_pinterest_candidates(geo=geo)
        tik = fetch_tiktok_candidates(geo=geo)

        stats["candidates_raw"] = {"google_trends": len(trends), "pinterest": len(pin), "tiktok": len(tik)}

        merged = merge_candidates(trends + pin + tik)
        stats["candidates_merged"] = len(merged)

        # 2) Score
        scored: List[Dict[str, Any]] = []
        for c in merged:
            s = score_candidate(c)
            c["score"] = s["score"]
            c["score_breakdown"] = s["score_breakdown"]
            scored.append(c)

        scored.sort(key=lambda x: x["score"], reverse=True)
        winners = scored[:topN]
        stats["topN"] = len(winners)

        # 3) AI + format rows for DB
        rows = []
        for w in winners:
            title = w["title"]
            slug = slugify(title)[:80]

            tags = w.get("tags", [])
            if not tags:
                # cheap tags from words
                tags = [t for t in slug.split("-")[:4] if t]

            # category default
            category = w.get("category") or "autre"

            analysis = generate_analysis(
                {
                    "title": title,
                    "category": category,
                    "tags": tags,
                    "sources": w.get("sources", []),
                    "signals": w.get("signals", {}),
                },
                geo=geo,
            )

            summary = ""
            try:
                summary = analysis.get("positioning", {}).get("main_promise", "") or ""
            except Exception:
                summary = ""

            rows.append({
                "run_date": run_date,
                "title": title,
                "slug": slug,
                "category": category,
                "tags": tags,              # text[]
                "sources": [
                    "google_trends" if "google_trends" in (w.get("sources") or []) else None,
                    "pinterest" if "pinterest" in (w.get("sources") or []) else None,
                    "tiktok" if "tiktok" in (w.get("sources") or []) else None,
                ],
                "score": int(w["score"]),
                "score_breakdown": w.get("score_breakdown", {}),
                "summary": summary,
                "signals": w.get("signals", {}),
                "analysis": analysis,
                "image_url": w.get("image_url"),
                "image_source": w.get("image_source"),
                "source_url": w.get("source_url"),
                "is_hidden": False,
                "published_at": utc_now_iso(),
            })

        # clean None from sources (text[])
        for r in rows:
            r["sources"] = [s for s in (r["sources"] or []) if s is not None]

        # 4) Push DB
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