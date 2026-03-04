from __future__ import annotations
from typing import Any, Dict, List
from pytrends.request import TrendReq

# On vise du volume pour que les filtres puissent travailler
MIN_CANDIDATES = 200

# Seeds e-commerce plus orientées "produits"
BROAD_SEEDS = [
    "tiktok gadget",
    "viral gadget",
    "amazon finds",
    "beauty gadget",
    "skincare device",
    "kitchen gadget",
    "home gadget",
    "pet gadget",
    "car gadget",
    "cleaning gadget",
    "smart home gadget",
    "portable blender",
    "mini vacuum",
]

BAD_TERMS = [
    "mots fléchés",
    "mots croisés",
    "synonyme",
    "solution",
    "définition",
    "definition",
    "3 lettres",
    "4 lettres",
    "5 lettres",
    "6 lettres",
    "7 lettres",
    "8 lettres",
    "10 lettres",
]

# Trop générique (souvent des catégories et du bruit)
GENERIC_TERMS = [
    "accessoire",
    "produit",
    "objet",
    "article",
    "équipement",
    "equipement",
    "outil",
]

# SEO / contenus (pas des produits)
SEO_TERMS = [
    "best ",
    "top ",
    "review",
    "reviews",
    "comparison",
    "compare",
    "vs",
    "guide",
    "how to",
    "comment",
    "avis",
    "test",
    "meilleur",
    "meilleurs",
    "comparatif",
]


def _is_bad_term(term: str) -> bool:
    t = (term or "").strip().lower()
    if not t:
        return True

    if any(x in t for x in BAD_TERMS):
        return True

    # évite les requêtes SEO type "best home weather stations"
    if any(x in t for x in SEO_TERMS):
        return True

    # évite "accessoire X" court
    if any(x in t for x in GENERIC_TERMS) and len(t.split()) <= 3:
        return True

    # trop court => souvent pas un produit
    if len(t.split()) <= 2:
        return True

    return False


def _interest_max(pytrends: TrendReq, term: str, geo: str, timeframe: str) -> int:
    try:
        pytrends.build_payload([term], geo=geo, timeframe=timeframe)
        it = pytrends.interest_over_time()
        if it is not None and not it.empty and term in it.columns:
            return int(it[term].max())
    except Exception:
        pass
    return 0


def _related_queries(pytrends: TrendReq, seed: str, cap_top: int, cap_rising: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        related = pytrends.related_queries()
        data = related.get(seed, {}) or {}

        top = data.get("top")
        rising = data.get("rising")

        def add_df(df, kind: str, cap: int):
            if df is None:
                return
            for _, row in df.head(cap).iterrows():
                q = str(row.get("query", "")).strip()
                if not q:
                    continue
                if _is_bad_term(q):
                    continue
                out.append({"query": q, "kind": kind})

        add_df(top, "top", cap_top)
        add_df(rising, "rising", cap_rising)

    except Exception:
        pass

    # dédup interne
    seen = set()
    dedup: List[Dict[str, Any]] = []
    for x in out:
        key = x["query"].lower()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(x)
    return dedup


def fetch_google_trends_candidates(geo: str = "FR", limit_trending: int = 40) -> List[Dict[str, Any]]:
    """
    V1 stable:
      1) trending_searches (France)
      2) related queries top + rising (cap plus grand)
      3) fallback seeds e-commerce (cap plus grand)
      4) timeframe adaptatif si trop peu de résultats
    """
    pytrends = TrendReq(hl="fr-FR", tz=60)

    # on essaye d'abord "1 mois", puis on élargit si trop pauvre
    timeframes = ["today 1-m", "today 3-m"]

    candidates: List[Dict[str, Any]] = []

    for timeframe in timeframes:
        candidates = []

        # 1) Trending searches FR
        trends: List[str] = []
        try:
            df = pytrends.trending_searches(pn="france")
            trends = [str(x).strip() for x in df[0].tolist() if str(x).strip()][:limit_trending]
        except Exception:
            trends = []

        for trend in trends:
            interest = _interest_max(pytrends, trend, geo, timeframe)

            # IMPORTANT: il faut build_payload avant related_queries()
            try:
                pytrends.build_payload([trend], geo=geo, timeframe=timeframe)
            except Exception:
                pass

            rel = _related_queries(pytrends, trend, cap_top=25, cap_rising=25)

            for item in rel:
                q = item["query"]
                candidates.append(
                    {
                        "title": q,
                        "sources": ["google_trends"],
                        "signals": {
                            "google_trends": {
                                "seed": trend,
                                "kind": item["kind"],
                                "interest": interest,
                                "timeframe": timeframe,
                            }
                        },
                    }
                )

        # 2) Fallback seeds si pas assez
        if len(candidates) < MIN_CANDIDATES:
            for seed in BROAD_SEEDS:
                interest = _interest_max(pytrends, seed, geo, timeframe)

                try:
                    pytrends.build_payload([seed], geo=geo, timeframe=timeframe)
                except Exception:
                    pass

                rel = _related_queries(pytrends, seed, cap_top=25, cap_rising=25)

                for item in rel:
                    q = item["query"]
                    candidates.append(
                        {
                            "title": q,
                            "sources": ["google_trends"],
                            "signals": {
                                "google_trends": {
                                    "seed": seed,
                                    "kind": f"fallback_{item['kind']}",
                                    "interest": interest,
                                    "timeframe": timeframe,
                                }
                            },
                        }
                    )

        # Dédup global
        seen = set()
        deduped: List[Dict[str, Any]] = []
        for c in candidates:
            k = c["title"].strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            deduped.append(c)

        candidates = deduped

        if len(candidates) >= MIN_CANDIDATES:
            break

    return candidates