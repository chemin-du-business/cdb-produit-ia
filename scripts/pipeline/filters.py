import re
from typing import Any, Dict, List
from scripts.pipeline.ai import classify_product_gate


BANNED_PATTERNS = [
    r"\bprésident\b", r"\bpolitique\b", r"\bélection\b", r"\bfoot\b", r"\bmatch\b",
    r"\bnba\b", r"\bnfl\b", r"\bguerre\b", r"\bcrypto\b", r"\bbourse\b",
]
BANNED_RE = re.compile("|".join(BANNED_PATTERNS), re.IGNORECASE)

TOO_SHORT = 3


def basic_candidate_filter(title: str) -> bool:
    t = (title or "").strip()
    if len(t) < TOO_SHORT:
        return False
    if BANNED_RE.search(t):
        return False
    # very generic non-product trend terms
    if t.lower() in {"meteo", "weather", "news", "actualité"}:
        return False
    return True


def ai_product_gate(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls OpenAI once to:
    - decide if the term corresponds to a sellable e-commerce product
    - propose a category + tags
    """
    title = item.get("title", "")
    signals = item.get("signals", {})
    return classify_product_gate(title=title, signals=signals)