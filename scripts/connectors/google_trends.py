from __future__ import annotations
from typing import Any, Dict, List
from pytrends.request import TrendReq

MIN_CANDIDATES = 30

BROAD_SEEDS = [
    "accessoire", "outil", "gadgets", "maison", "cuisine", "beauté",
    "sport", "fitness", "bébé", "animaux", "voiture", "bureau"
]

def _interest_max(pytrends: TrendReq, term: str, geo: str, timeframe: str) -> int:
    try:
        pytrends.build_payload([term], geo=geo, timeframe=timeframe)
        it = pytrends.interest_over_time()
        if it is not None and not it.empty and term in it.columns:
            return int(it[term].max())
    except Exception:
        pass
    return 0

def _related_queries(pytrends: TrendReq, seed: str, cap: int = 10) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        related = pytrends.related_queries()
        data = related.get(seed, {})
        top = data.get("top")
        rising = data.get("rising")

        def add_df(df, kind: str):
            if df is None:
                return
            for _, row in df.head(cap).iterrows():
                q = str(row.get("query", "")).strip()
                if q:
                    out.append({"query": q, "kind": kind})

        add_df(top, "top")
        add_df(rising, "rising")
    except Exception:
        pass
    return out

def fetch_google_trends_candidates(geo: str = "FR", limit_trending: int = 25) -> List[Dict[str, Any]]:
    """
    Primary:
      - trending_searches France (actuel)
      - for each trend: related queries -> candidates
    Fallback:
      - broad seeds -> related queries
    """
    pytrends = TrendReq(hl="fr-FR", tz=60)
    timeframe = "today 1-m"

    candidates: List[Dict[str, Any]] = []

    # 1) Trending searches FR (actuel)
    trends: List[str] = []
    try:
        df = pytrends.trending_searches(pn="france")
        trends = [str(x).strip() for x in df[0].tolist()][:limit_trending]
    except Exception:
        trends = []

    for trend in trends:
        if not trend:
            continue
        interest = _interest_max(pytrends, trend, geo, timeframe)
        rel = _related_queries(pytrends, trend, cap=10)
        for item in rel:
            q = item["query"]
            candidates.append({
                "title": q,
                "sources": ["google_trends"],
                "signals": {
                    "google_trends": {
                        "seed": trend,
                        "kind": item["kind"],   # top/rising
                        "interest": interest,   # 0..100
                        "timeframe": timeframe
                    }
                }
            })

    # 2) Fallback si trop peu
    if len(candidates) < MIN_CANDIDATES:
        for seed in BROAD_SEEDS:
            interest = _interest_max(pytrends, seed, geo, timeframe)
            rel = _related_queries(pytrends, seed, cap=10)
            for item in rel:
                q = item["query"]
                candidates.append({
                    "title": q,
                    "sources": ["google_trends"],
                    "signals": {
                        "google_trends": {
                            "seed": seed,
                            "kind": f"fallback_{item['kind']}",
                            "interest": interest,
                            "timeframe": timeframe
                        }
                    }
                })

    return candidates