from __future__ import annotations

import os
import json
import time
import random
from typing import Any, Dict, List
from openai import OpenAI, InternalServerError, RateLimitError, APITimeoutError

client = OpenAI(api_key=(os.environ.get("OPENAI_API_KEY") or "").strip())


def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"


# ---------- OPENAI RETRY ----------

def _sleep_backoff(attempt: int):
    base = min(2 ** attempt, 20)
    time.sleep(base + random.random())


def _chat_with_retry(**kwargs):
    last_error = None

    for attempt in range(6):
        try:
            return client.chat.completions.create(**kwargs)

        except (InternalServerError, RateLimitError, APITimeoutError) as e:
            last_error = e
            _sleep_backoff(attempt)

    raise last_error


# ---------- UTILS ----------

def _safe_json_load(s: str) -> Dict[str, Any]:
    s = (s or "").strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        pass
    try:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(s[start:end + 1])
    except Exception:
        pass
    return {}


def _ensure_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _ensure_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _clean_str(x: Any) -> str:
    s = (str(x) if x is not None else "").strip()
    if s in ("...", "…"):
        return ""
    return s


def _coerce_int(x: Any, default: int) -> int:
    try:
        if x is None or isinstance(x, bool):
            return default
        if isinstance(x, (int, float)):
            return int(x)
        return int(float(str(x).replace(",", ".")))
    except Exception:
        return default


def _coerce_float(x: Any, default: float) -> float:
    try:
        if x is None or isinstance(x, bool):
            return default
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).replace("€", "").replace(",", ".")
        return float(s)
    except Exception:
        return default


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _uniq_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for it in items:
        t = _clean_str(it)
        if not t:
            continue
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(t)
    return out


# ---------- AI HELPERS ----------

def extract_product_name(caption: str, geo: str = "FR") -> str:
    caption = (caption or "").strip()
    if not caption:
        return ""

    resp = _chat_with_retry(
        model=_model(),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extrait UN SEUL nom de produit e-commerce concret depuis une caption TikTok. "
                    "Réponds uniquement par le nom (2 à 6 mots), en français si possible. "
                    "Si aucun produit clair : RIEN."
                ),
            },
            {"role": "user", "content": f"Caption: {caption}\nMarché: {geo}"},
        ],
    )

    txt = (resp.choices[0].message.content or "").strip()

    if txt.upper().startswith("RIEN"):
        return ""

    return txt[:80]


def is_sellable_product(term: str, geo: str = "FR") -> bool:
    term = (term or "").strip()
    if not term:
        return False

    resp = _chat_with_retry(
        model=_model(),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Réponds uniquement par OUI ou NON. "
                    "OUI seulement si c'est un produit e-commerce concret vendable."
                ),
            },
            {"role": "user", "content": f"Terme: {term} (marché {geo})"},
        ],
    )

    txt = (resp.choices[0].message.content or "").strip().upper()

    return txt.startswith("OUI")


# ---------- FALLBACK ANALYSIS ----------

def _default_analysis(title: str) -> Dict[str, Any]:
    return {
        "risks": [
            {
                "note": "Concurrence possible sur ce type de produit.",
                "type": "concurrence",
                "level": "medium",
            }
        ],
        "angles": {
            "hooks": [
                f"Tout le monde parle de {title}… et tu vas comprendre pourquoi",
                f"Le truc simple qui rend {title} beaucoup plus efficace",
                f"Si tu as déjà galéré avec [problème], {title} peut te sauver",
            ],
            "objections": [
                {
                    "objection": "Ça a l’air gadget",
                    "response": "On montre la démo avant/après en 5 secondes.",
                },
                {
                    "objection": "Je ne sais pas si ça marche",
                    "response": "Preuve sociale + vidéo UGC.",
                },
            ],
            "ugc_script": {
                "script": (
                    f"J’avais un problème avec [problème]… puis j’ai testé {title}. "
                    "Regarde la différence en 5 secondes."
                ),
                "duration_seconds": 20,
            },
        },
        "confidence": {
            "score": 6,
            "reasons": [
                "Signal TikTok observé",
                "Produit simple à comprendre en vidéo",
            ],
        },
        "positioning": {
            "why_now": "Les formats UGC courts boostent les produits démontrables.",
            "main_promise": "Résultat visible rapidement avec un usage simple.",
            "problem_solved": "Résout un irritant du quotidien.",
            "target_customer": "Public 18-45 acheteurs impulsifs.",
        },
        "recommendations": {
            "upsells": ["Accessoires", "Bundle"],
            "channels": ["TikTok Ads", "UGC", "Retargeting"],
            "price_range": {"min": 19, "max": 49, "currency": "EUR"},
        },
    }


# ---------- GENERATE ANALYSIS ----------

def generate_analysis(payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:

    title = (payload.get("title") or "").strip()

    if not title:
        return _default_analysis("ce produit")

    system = (
        "Tu es un expert e-commerce FR et copywriter TikTok. "
        "Retourne UNIQUEMENT un JSON complet et spécifique au produit."
    )

    resp = _chat_with_retry(
        model=_model(),
        temperature=0.8,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )

    txt = (resp.choices[0].message.content or "").strip()

    data = _safe_json_load(txt)

    if not data:
        return _default_analysis(title)

    return data