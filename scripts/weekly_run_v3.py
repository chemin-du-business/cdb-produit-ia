from __future__ import annotations
import os
from datetime import date
from typing import Any, Dict, List
from slugify import slugify

from scripts.connectors.tiktok_hashtag_apify import fetch_tiktok_candidates_from_hashtags
from scripts.connectors.pinterest import fetch_pinterest_signal
from scripts.pipeline.merge import merge_candidates
from scripts.pipeline.scoring import score_candidate
from scripts.pipeline.supabase_db import get_supabase, upsert_products
from scripts.pipeline.ai import extract_product_name, is_sellable_product, generate_analysis

TOP_N=int(os.environ.get("TOP_N","20"))
REGION=os.environ.get("RUN_REGION","FR")

def main():
    sb=get_supabase()

    raw=fetch_tiktok_candidates_from_hashtags()
    merged=merge_candidates(raw)

    sellable=[]
    for c in merged:
        caption=c.get("title","")
        product=extract_product_name(caption, geo=REGION)
        if not product:
            continue
        if not is_sellable_product(product, geo=REGION):
            continue
        c["title"]=product
        sellable.append(c)

    enriched=[]
    for c in sellable:
        title=c["title"]
        c.setdefault("signals",{})
        pin=fetch_pinterest_signal(title)
        c["signals"]["pinterest"]=pin
        if int(pin.get("hits",0) or 0) > 0:
            if "pinterest" not in (c.get("sources") or []):
                c["sources"].append("pinterest")
            c["image_url"]=pin.get("image_url")
            c["image_source"]="pinterest"
            c["source_url"]=pin.get("source_url")

        enriched.append(c)

    # scoring max
    max_views=max([int((x.get("signals",{}).get("tiktok_hashtag",{}).get("views",0) or 0)) for x in enriched] + [1])
    max_likes=max([int((x.get("signals",{}).get("tiktok_hashtag",{}).get("likes",0) or 0)) for x in enriched] + [1])
    max_shares=max([int((x.get("signals",{}).get("tiktok_hashtag",{}).get("shares",0) or 0)) for x in enriched] + [1])

    for c in enriched:
        s=score_candidate(c,max_views=max_views,max_likes=max_likes,max_shares=max_shares)
        c["score"]=s["score"]
        c["score_breakdown"]=s["score_breakdown"]

    enriched.sort(key=lambda x:x.get("score",0), reverse=True)
    winners=enriched[:TOP_N]

    rows=[]
    for w in winners:
        title=w["title"]
        analysis=generate_analysis({
            "title": title,
            "category": "autre",
            "tags": [t for t in slugify(title).split("-")[:4] if t],
            "sources": w.get("sources",[]),
            "signals": w.get("signals",{}),
        }, geo=REGION)

        rows.append({
            "run_date": str(date.today()),
            "title": title,
            "slug": slugify(title)[:80],
            "category": "autre",
            "tags": [t for t in slugify(title).split("-")[:4] if t],
            "sources": w.get("sources",[]),
            "score": int(w.get("score",0)),
            "score_breakdown": w.get("score_breakdown",{}),
            "summary": (analysis.get("positioning",{}) or {}).get("main_promise","") or "",
            "signals": w.get("signals",{}),
            "analysis": analysis,
            "image_url": w.get("image_url"),
            "image_source": w.get("image_source"),
            "source_url": w.get("source_url") or (w.get("signals",{}).get("tiktok_hashtag",{}).get("video_url")),
            "is_hidden": False,
        })

    upsert_products(sb, rows)
    print("OK ✅", {"run_date": str(date.today()), "region": REGION, "candidates_raw": len(raw), "candidates_merged": len(merged), "candidates_sellable": len(sellable), "candidates_enriched": len(enriched), "topN": len(winners)})

if __name__=="__main__":
    main()
