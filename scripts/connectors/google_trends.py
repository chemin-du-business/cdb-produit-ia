"""Connecteur Google Trends via SerpApi."""
from __future__ import annotations

from typing import Any, Dict, List

from .serpapi_client import serpapi_get


def fetch_google_trends(
    keywords: List[str],
    geo: str = "FR",
    timeframe: str = "today 3-m",
) -> List[Dict[str, Any]]:
    """
    Retourne pour chaque keyword :
    - interest_over_time (liste de {date, value})
    - rising_queries (liste de {query, value})
    - top_queries (liste de {query, value})
    - trend_direction : "rising" | "stable" | "declining"
    """
    results = []

    for kw in keywords:
        try:
            data = serpapi_get(
                engine="google_trends",
                params={
                    "q": kw,
                    "geo": geo,
                    "date": timeframe,
                    "data_type": "TIMESERIES",
                },
            )

            timeline = data.get("interest_over_time", {}).get("timeline_data", [])
            values = [point.get("values", [{}])[0].get("extracted_value", 0) for point in timeline]

            # direction : compare première moitié vs deuxième moitié
            mid = len(values) // 2
            if mid > 0 and values:
                first_half = sum(values[:mid]) / mid
                second_half = sum(values[mid:]) / max(len(values[mid:]), 1)
                if second_half > first_half * 1.15:
                    direction = "rising"
                elif second_half < first_half * 0.85:
                    direction = "declining"
                else:
                    direction = "stable"
            else:
                direction = "stable"

            # Related queries
            related = data.get("related_queries", {})
            rising_q = [
                {"query": r.get("query", ""), "value": r.get("extracted_value", r.get("value", 0))}
                for r in (related.get("rising") or [])[:5]
            ]
            top_q = [
                {"query": r.get("query", ""), "value": r.get("extracted_value", r.get("value", 0))}
                for r in (related.get("top") or [])[:5]
            ]

            current_value = values[-1] if values else 0
            peak_value = max(values) if values else 0

            results.append({
                "keyword": kw,
                "geo": geo,
                "current_value": current_value,
                "peak_value": peak_value,
                "trend_direction": direction,
                "rising_queries": rising_q,
                "top_queries": top_q,
                "timeline": [
                    {"date": p.get("date", ""), "value": v}
                    for p, v in zip(timeline, values)
                ],
            })

        except Exception as e:
            print(f"[google_trends] erreur pour '{kw}': {e}")
            results.append({
                "keyword": kw,
                "geo": geo,
                "current_value": 0,
                "peak_value": 0,
                "trend_direction": "unknown",
                "rising_queries": [],
                "top_queries": [],
                "timeline": [],
                "error": str(e),
            })

    return results
