from __future__ import annotations
from typing import Any, Dict, List
from pytrends.request import TrendReq

def fetch_google_trends_candidates(geo: str = "FR", seeds: List[str] | None = None) -> List[Dict[str, Any]]:
    """
    V1 simple:
    - Pour chaque seed, on récupère related_queries (top/rising)
    - On crée des candidats = keywords
    """
    if seeds is None:
        seeds = ["gourde", "brosse visage", "lampe led", "fitness", "cuisine", "maison", "beauté"]

    pytrends = TrendReq(hl="fr-FR", tz=60)
    candidates: List[Dict[str, Any]] = []

    for seed in seeds:
        try:
            pytrends.build_payload([seed], geo=geo, timeframe="now 7-d")
            related = pytrends.related_queries()
            data = related.get(seed, {})
            top = data.get("top")
            rising = data.get("rising")

            # Basic interest (0..100) for the seed
            interest = 0
            try:
                it = pytrends.interest_over_time()
                if it is not None and not it.empty and seed in it.columns:
                    interest = int(it[seed].max())
            except Exception:
                interest = 0

            def add_from_df(df, kind: str):
                if df is None:
                    return
                for _, row in df.head(10).iterrows():
                    kw = str(row.get("query", "")).strip()
                    if not kw:
                        continue
                    candidates.append({
                        "title": kw,
                        "sources": ["google_trends"],
                        "signals": {"google_trends": {"seed": seed, "kind": kind, "interest": interest}},
                    })

            add_from_df(top, "top")
            add_from_df(rising, "rising")

        except Exception:
            # ignore a seed if it fails
            continue

    return candidates