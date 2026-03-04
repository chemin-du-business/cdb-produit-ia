from __future__ import annotations

import os
from datetime import date
from typing import Dict, List
from slugify import slugify

from scripts.connectors.tiktok_hashtag_apify import fetch_tiktok_candidates_from_hashtags
from scripts.pipeline.merge import merge_candidates
from scripts.pipeline.scoring import score_candidate
from scripts.pipeline.supabase_db import get_supabase, upsert_products, upload_video
from scripts.pipeline.ai import extract_product_name, is_sellable_product, generate_analysis

TOP_N = int(os.environ.get("TOP_N", "20"))
REGION = os.environ.get("RUN_REGION", "FR")


def _norm_text(s: str) -> str:
    return (s or "").lower().replace("’", "'").strip()


def infer_category(title: str) -> str:
    t = _norm_text(title)

    rules = [
        ("beauté", ["skincare", "peau", "visage", "lèvre", "levres", "cheveux", "anti-âge", "anti age", "serum", "sérum", "crème", "creme", "masque", "brosse visage", "épilation", "epilation", "manucure"]),
        ("fitness", ["fitness", "muscu", "musculation", "running", "sport", "yoga", "pilates", "shaker", "gourde", "ceinture", "gainage", "corde à sauter", "corde a sauter"]),
        ("cuisine", ["cuisine", "air fryer", "friteuse", "poêle", "poele", "mixeur", "blender", "hacheur", "râpe", "rape", "couteau", "moule", "boîte", "boite", "lunch box"]),
        ("maison", ["maison", "déco", "deco", "rangement", "placard", "organisation", "aspirateur", "balai", "nettoyage", "lampe", "led", "veilleuse", "projecteur", "humidificateur"]),
        ("animaux", ["chien", "chat", "animal", "animaux", "litière", "litiere", "laisse", "harnais", "gamelle", "brosse pour chat", "brosse chien"]),
        ("bébé", ["bébé", "bebe", "enfant", "nouveau-né", "nouveau ne", "poussette", "biberon", "veilleuse bébé", "maman"]),
        ("auto", ["voiture", "auto", "moto", "car", "téléphone voiture", "support téléphone", "support telephone", "dashcam", "parking", "nettoyage voiture"]),
        ("bureau", ["bureau", "pc", "ordinateur", "clavier", "souris", "support pc", "support ordinateur", "câble", "cable", "organisation bureau"]),
        ("mode", ["montre", "bracelet", "collier", "bague", "lunettes", "sac", "chaussures", "casquette", "vêtement", "vetement"]),
        ("high-tech", ["bluetooth", "écouteurs", "ecouteurs", "chargeur", "power bank", "batterie externe", "caméra", "camera", "projecteur", "smart", "tracker", "gps"]),
    ]

    for cat, kws in rules:
        if any(k in t for k in kws):
            return cat

    return "autre"


def make_tags(title: str) -> List[str]:
    return [w for w in slugify(title).split("-")[:6] if w]


def main() -> None:
    sb = get_supabase()
    run_date = str(date.today())

    raw = fetch_tiktok_candidates_from_hashtags()
    merged = merge_candidates(raw)

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

    # scoring max (sur sellable)
    max_views = max([int((x.get("signals", {}).get("tiktok_hashtag", {}).get("views", 0) or 0)) for x in sellable] + [1])
    max_likes = max([int((x.get("signals", {}).get("tiktok_hashtag", {}).get("likes", 0) or 0)) for x in sellable] + [1])
    max_shares = max([int((x.get("signals", {}).get("tiktok_hashtag", {}).get("shares", 0) or 0)) for x in sellable] + [1])

    for c in sellable:
        s = score_candidate(c, max_views=max_views, max_likes=max_likes, max_shares=max_shares)
        c["score"] = s["score"]
        c["score_breakdown"] = s["score_breakdown"]

        title = c["title"]
        c["category"] = infer_category(title)
        c["tags"] = make_tags(title)

    sellable.sort(key=lambda x: x.get("score", 0), reverse=True)
    winners = sellable[:TOP_N]

    rows: List[Dict] = []
    for w in winners:
        title = w["title"]
        category = w.get("category", "autre")
        tags = w.get("tags", [])

        video_download = (
            w.get("signals", {})
            .get("tiktok_hashtag", {})
            .get("video_download")
        )

        video_storage_url = None
        video_path = None

        if video_download:
            try:
                video_path = f"{run_date}/{slugify(title)}.mp4"
                video_storage_url = upload_video(sb, video_download, video_path)
            except Exception as e:
                print("video upload failed", e)

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

        rows.append(
            {
                "run_date": run_date,
                "title": title,
                "slug": slugify(title)[:80],
                "category": category,
                "tags": tags,
                "sources": w.get("sources", []),
                "score": int(w.get("score", 0)),
                "score_breakdown": w.get("score_breakdown", {}),
                "summary": summary,
                "signals": w.get("signals", {}),
                "analysis": analysis,
                "image_url": None,
                "image_source": None,
                "source_url": (w.get("signals", {}).get("tiktok_hashtag", {}) or {}).get("video_url"),
                "video_storage_url": video_storage_url,
                "video_path": video_path,
                "is_hidden": False,
            }
        )

    upsert_products(sb, rows)

    print(
        "OK ✅",
        {
            "run_date": run_date,
            "region": REGION,
            "candidates_raw": len(raw),
            "candidates_merged": len(merged),
            "candidates_sellable": len(sellable),
            "topN": len(winners),
        },
    )


if __name__ == "__main__":
    main()