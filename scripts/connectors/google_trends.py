import os
from typing import Dict, List, Any, Optional
from pytrends.request import TrendReq

BROAD_SEEDS = [
    "accessoire", "outil", "gadget", "maison", "cuisine", "beauté",
    "sport", "fitness", "bébé", "animaux", "voiture", "bureau",
    "voyage", "santé", "wellness", "organisation", "rangement"
]


def _pytrends() -> TrendReq:
    return TrendReq(hl="fr-FR", tz=360)


def _trending_terms(geo: str) -> List[str]:
    # pytrends trending_searches supports some pn values (e.g., "france")
    # If geo is FR -> pn="france", else fallback.
    pn = "france" if geo.upper() == "FR" else "united_states"
    df = _pytrends().trending_searches(pn=pn)
    return [str(x).strip() for x in df[0].tolist() if str(x).strip()]


def _related_queries(seed: str, geo: str) -> List[str]:
    pt = _pytrends()
    pt.build_payload([seed], timeframe="now 7-d", geo=geo.upper())
    rq = pt.related_queries()
    out: List[str] = []
    try:
        top = rq.get(seed, {}).get("top")
        if top is not None:
            for q in top["query"].tolist():
                if isinstance(q, str) and q.strip():
                    out.append(q.strip())
    except Exception:
        pass
    return out


def enrich_single(title: str, geo: str) -> Dict[str, Any]:
    """
    Returns a compact signal for scoring:
    - interest_score (0-100): normalized by peak
    - peak: max interest
    - avg: average interest
    - slope: last - first (trend direction)
    """
    pt = _pytrends()
    pt.build_payload([title], timeframe="now 7-d", geo=geo.upper())
    df = pt.interest_over_time()

    if df is None or df.empty or title not in df.columns:
        return {"interest_score": 0, "peak": 0, "avg": 0, "slope": 0}

    series = df[title].astype(float).tolist()
    peak = max(series) if series else 0
    avg = sum(series) / len(series) if series else 0
    slope = (series[-1] - series[0]) if len(series) >= 2 else 0

    interest_score = 0
    if peak > 0:
        # combine avg and slope lightly
        interest_score = min(100, int((avg / peak) * 70 + max(0, slope) * 0.3))

    return {
        "interest_score": int(interest_score),
        "peak": int(peak),
        "avg": int(avg),
        "slope": float(round(slope, 3)),
        "timeframe": "now 7-d",
        "geo": geo.upper(),
    }


def fetch_google_trends_candidates(geo: str = "FR", min_candidates: int = 40) -> List[str]:
    """
    1) Pull trending searches
    2) If insufficient, expand using related queries from broad seeds
    """
    seen = set()

    base = _trending_terms(geo=geo)
    out: List[str] = []
    for t in base:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            out.append(t)

    # fallback
    if len(out) < min_candidates:
        for seed in BROAD_SEEDS:
            for q in _related_queries(seed, geo=geo):
                key = q.lower()
                if key not in seen:
                    seen.add(key)
                    out.append(q)
                if len(out) >= min_candidates:
                    break
            if len(out) >= min_candidates:
                break

    return out


# allow weekly_run to call enrich_single via attribute access
fetch_google_trends_candidates.enrich_single = enrich_single  # type: ignore[attr-defined]