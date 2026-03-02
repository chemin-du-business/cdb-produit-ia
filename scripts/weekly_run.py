import os
import json
import time
from datetime import date
from typing import Any, Dict, List

from scripts.connectors.google_trends import fetch_google_trends_candidates
from scripts.connectors.tiktok_rapidapi import fetch_tiktok_signal
from scripts.connectors.pinterest_rapidapi import fetch_pinterest_signal
from scripts.connectors.image_downloader import download_image_bytes
from scripts.pipeline.filters import (
    basic_candidate_filter,
    ai_product_gate,
)
from scripts.pipeline.scoring import score_candidate
from scripts.pipeline.diversity import diversify_top_n
from scripts.pipeline.ai import generate_analysis_json
from scripts.pipeline.db import (
    upsert_product,
    upsert_run,
    upload_image_to_storage,
)
from scripts.pipeline.utils import make_slug, now_iso, safe_int


DEFAULT_LIMIT = 10


def main():
    run_date = date.today().isoformat()
    started_at = time.time()

    limit = int(os.environ.get("TRENDING_LIMIT", DEFAULT_LIMIT))
    geo = os.environ.get("TRENDS_GEO", "FR")
    cold_mode = os.environ.get("COLD_MODE", "0") == "1"

    stats: Dict[str, Any] = {
        "mode": "trending",
        "geo": geo,
        "limit": limit,
        "started_at": now_iso(),
        "cold_mode": cold_mode,
    }
    errors: List[Dict[str, Any]] = []

    # 1) get candidates from trends (+ fallback seeds inside)
    candidates = fetch_google_trends_candidates(geo=geo, min_candidates=40)
    stats["candidates_raw"] = len(candidates)

    # 2) basic filtering (no AI yet)
    candidates = [c for c in candidates if basic_candidate_filter(c)]
    stats["candidates_after_basic_filter"] = len(candidates)

    # 3) Enrich & score each candidate (multi-source)
    scored: List[Dict[str, Any]] = []

    for title in candidates:
        try:
            slug = make_slug(title)
            item: Dict[str, Any] = {
                "title": title,
                "slug": slug,
                "sources": ["google_trends"],
                "signals": {},
            }

            if cold_mode:
                # minimal fake signals for debug
                item["signals"]["google_trends"] = {"interest_score": 55, "peak": 72, "avg": 33, "slope": 0.4}
                item["signals"]["tiktok"] = {"posts": 5, "views_median": 12000, "views_top": 90000, "likes_median": 900}
                item["signals"]["pinterest"] = {"pins": 12, "best_image_url": None}
            else:
                gt = fetch_google_trends_candidates.enrich_single(title=title, geo=geo)  # type: ignore[attr-defined]
                item["signals"]["google_trends"] = gt

                tt = fetch_tiktok_signal(keyword=title)
                if tt.get("ok"):
                    item["signals"]["tiktok"] = tt["signal"]
                    item["sources"].append("tiktok")
                else:
                    item["signals"]["tiktok"] = {"error": tt.get("error", "unknown")}

                pin = fetch_pinterest_signal(keyword=title, num=int(os.environ.get("PIN_NUM", "30")))
                if pin.get("ok"):
                    item["signals"]["pinterest"] = pin["signal"]
                    item["sources"].append("pinterest")
                else:
                    item["signals"]["pinterest"] = {"error": pin.get("error", "unknown")}

            # 4) score
            scored_item = score_candidate(item)
            scored.append(scored_item)

        except Exception as e:
            errors.append({"title": title, "step": "score", "error": str(e)})

    stats["scored_total"] = len(scored)

    # 5) AI gate: product vendable (avant analyse longue)
    gated: List[Dict[str, Any]] = []
    for item in scored:
        try:
            gate = ai_product_gate(item)
            if not gate.get("ok"):
                # if AI fails, we keep but mark low confidence
                item["analysis_gate"] = {"ok": False, "reason": gate.get("error", "ai_gate_failed")}
                gated.append(item)
                continue

            if gate["is_product"] is True:
                item["category"] = gate.get("category", "autre")
                item["tags"] = gate.get("tags", [])
                item["analysis_gate"] = gate
                gated.append(item)
            else:
                # rejected
                continue

        except Exception as e:
            errors.append({"title": item.get("title"), "step": "ai_gate", "error": str(e)})

    stats["after_ai_gate"] = len(gated)

    # 6) sort by score & diversify
    gated.sort(key=lambda x: safe_int(x.get("score", 0)), reverse=True)
    final_items = diversify_top_n(gated, top_n=limit, max_per_category=2)
    stats["final_count"] = len(final_items)

    # 7) Generate full analysis + image download/upload + DB upsert
    inserted = 0
    for item in final_items:
        try:
            title = item["title"]
            slug = item["slug"]

            # Image: pinterest best image first
            best_image_url = None
            pin_sig = item.get("signals", {}).get("pinterest", {})
            if isinstance(pin_sig, dict):
                best_image_url = pin_sig.get("best_image_url")

            image_url_db = None
            image_source = None

            if best_image_url and not cold_mode:
                img_bytes, content_type = download_image_bytes(best_image_url)
                if img_bytes:
                    public_url = upload_image_to_storage(
                        slug=slug,
                        image_bytes=img_bytes,
                        content_type=content_type or "image/jpeg",
                    )
                    if public_url:
                        image_url_db = public_url
                        image_source = "pinterest"

            # AI analysis (UI JSON)
            analysis_json = generate_analysis_json(item)

            product_row = {
                "run_date": run_date,
                "title": title,
                "slug": slug,
                "category": item.get("category", "autre"),
                "tags": item.get("tags", []),
                "sources": item.get("sources", []),
                "score": int(item.get("score", 0)),
                "score_breakdown": item.get("score_breakdown", {}),
                "summary": analysis_json.get("summary", ""),
                "signals": item.get("signals", {}),
                "analysis": analysis_json,
                "image_url": image_url_db,
                "image_source": image_source,
                "source_url": analysis_json.get("source_url"),
                "published_at": None,
                "is_hidden": False,
            }

            upsert_product(product_row)
            inserted += 1

        except Exception as e:
            errors.append({"title": item.get("title"), "step": "db_upsert", "error": str(e)})

    stats["inserted"] = inserted
    stats["errors_count"] = len(errors)
    stats["runtime_sec"] = round(time.time() - started_at, 2)
    stats["finished_at"] = now_iso()

    # 8) run log
    status = "success"
    if errors and inserted > 0:
        status = "partial"
    if inserted == 0 and errors:
        status = "fail"

    upsert_run(run_date=run_date, status=status, stats=stats, errors=errors)

    print(json.dumps({"status": status, "stats": stats, "errors": errors[:3]}, ensure_ascii=False, indent=2))

    # fail CI if totally fail
    if status == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()