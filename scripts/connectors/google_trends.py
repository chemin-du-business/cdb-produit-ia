import os
from typing import Dict, List, Any
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError


BROAD_SEEDS = [
    "accessoire", "outil", "gadget", "maison", "cuisine", "beauté",
    "sport", "fitness", "bébé", "animaux", "voiture", "bureau",
    "voyage", "santé", "wellness", "organisation", "rangement",
    "skincare", "cheveux", "massage", "posture", "anti ride"
]

# mapping pytrends 'pn' values (kept for compatibility)
PN_BY_GEO = {
    "FR": "france",
    "US": "united_states",
    "GB": "united_kingdom",
    "DE": "germany",
    "ES": "spain",
    "IT": "italy",
}

# Lock France (as requested)
LOCKED_GEO = "FR"


def _pytrends() -> TrendReq:
    """
    CI-safe TrendReq.
    IMPORTANT: Do NOT pass "timeout" in requests_args
    because pytrends already passes timeout internally.
    """
    return TrendReq(
        hl="fr-FR",
        tz=60,  # Europe/Paris approx
        retries=3,
        backoff_factor=0.4,
        requests_args={
            "headers": {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
                )
            }
        },
    )


def _trending_terms(geo: str) -> List[str]:
    """
    CI-safe trending candidates.
    We DO NOT use trending_searches() (often 404 in CI).
    Instead:
      - realtime_trending_searches
      - today_searches
    """
    geo = LOCKED_GEO
    pt = _pytrends()
    out: List[str] = []

    # 1) Realtime trending (best signal)
    try:
        df_rt = pt.realtime_trending_searches(pn=geo)
        if df_rt is not None and not df_rt.empty:
            if "title" in df_rt.columns:
                out.extend([str(x).strip() for x in df_rt["title"].tolist() if str(x).strip()])
            else:
                out.extend([str(x).strip() for x in df_rt.iloc[:, 0].tolist() if str(x).strip()])
    except Exception:
        pass

    # 2) Daily trending (stable fallback)
    try:
        s = pt.today_searches(pn=geo)
        out.extend([str(x).strip() for x in s.tolist() if str(x).strip()])
    except Exception:
        pass

    # Deduplicate while preserving order
    seen = set()
    dedup: List[str] = []
    for t in out:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            dedup.append(t)

    return dedup


def _related_queries(seed: str, geo: str) -> List[str]:
    """
    Related queries are usually more stable.
    """
    geo = LOCKED_GEO
    pt = _pytrends()

    try:
        pt.build_payload([seed], timeframe="now 7-d", geo=geo)
        rq = pt.related_queries()
    except Exception:
        return []

    out: List[str] = []

    try:
        top = rq.get(seed, {}).get("top")
        if top is not None and "query" in top.columns:
            for q in top["query"].tolist():
                if isinstance(q, str) and q.strip():
                    out.append(q.strip())
    except Exception:
        pass

    return out


def enrich_single(title: str, geo: str) -> Dict[str, Any]:
    """
    Compact signal for scoring:
    - interest_score (0-100)
    - peak, avg, slope
    Timeframe: 7 days
    """
    geo = LOCKED_GEO
    pt = _pytrends()

    try:
        pt.build_payload([title], timeframe="now 7-d", geo=geo)
        df = pt.interest_over_time()
    except Exception:
        return {
            "interest_score": 0,
            "peak": 0,
            "avg": 0,
            "slope": 0,
            "timeframe": "now 7-d",
            "geo": geo,
        }

    if df is None or df.empty or title not in df.columns:
        return {
            "interest_score": 0,
            "peak": 0,
            "avg": 0,
            "slope": 0,
            "timeframe": "now 7-d",
            "geo": geo,
        }

    series = df[title].astype(float).tolist()

    peak = max(series) if series else 0
    avg = sum(series) / len(series) if series else 0
    slope = (series[-1] - series[0]) if len(series) >= 2 else 0

    interest_score = 0
    if peak > 0:
        interest_score = min(
            100,
            int((avg / peak) * 70 + max(0, slope) * 0.3)
        )

    return {
        "interest_score": int(interest_score),
        "peak": int(peak),
        "avg": int(avg),
        "slope": float(round(slope, 3)),
        "timeframe": "now 7-d",
        "geo": geo,
    }


def fetch_google_trends_candidates(geo: str = "FR", min_candidates: int = 40) -> List[str]:
    """
    1) Try trending candidates (CI-safe version)
    2) Fallback/complete using related queries from broad seeds
    """
    geo = LOCKED_GEO
    seen = set()
    out: List[str] = []

    # 1) Trending candidates
    base = _trending_terms(geo=geo)
    for t in base:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            out.append(t)

    # 2) Fallback seeds
    for seed in BROAD_SEEDS:
        if len(out) >= min_candidates:
            break

        for q in _related_queries(seed, geo=geo):
            key = q.lower()
            if key not in seen:
                seen.add(key)
                out.append(q)

            if len(out) >= min_candidates:
                break

    return out


# allow weekly_run to call enrich_single via attribute access
fetch_google_trends_candidates.enrich_single = enrich_single  # type: ignore[attr-defined]