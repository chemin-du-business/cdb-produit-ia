from __future__ import annotations
from typing import Any, Dict, List
from pytrends.request import TrendReq

MIN_CANDIDATES = 30

ECOM_SEEDS = [
    "produit viral tiktok",
    "produit tendance",
    "gadget tendance",
    "nouveauté maison pratique",
    "accessoire cuisine astucieux",
    "innovation maison",
    "accessoire voiture pratique",
    "accessoire bureau ergonomique",
    "produit beauté tendance",
    "accessoire cheveux tendance",
    "accessoire téléphone pratique",
    "objet anti stress tendance",
    "produit sport maison tendance",
    "accessoire voyage pratique",
    "idée cadeau utile",
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
    pytrends = TrendReq(hl="fr-FR", tz=60)
    timeframe = "today 1-m"
    candidates: List[Dict[str, Any]] = []

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
            candidates.append({
                "title": item["query"],
                "sources": ["google_trends"],
                "signals": {
                    "google_trends": {
                        "seed": trend,
                        "kind": item["kind"],
                        "interest": interest,
                        "timeframe": timeframe
                    }
                }
            })

    if len(candidates) < MIN_CANDIDATES:
        for seed in ECOM_SEEDS:
            interest = _interest_max(pytrends, seed, geo, timeframe)
            rel = _related_queries(pytrends, seed, cap=10)
            for item in rel:
                candidates.append({
                    "title": item["query"],
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