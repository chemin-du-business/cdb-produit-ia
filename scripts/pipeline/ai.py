from __future__ import annotations

import os
import json
import time
import random
import re
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI, InternalServerError, RateLimitError, APITimeoutError

# =============================================================================
# CONFIG
# =============================================================================

client = OpenAI(api_key=(os.environ.get("OPENAI_API_KEY") or "").strip())

def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"


# =============================================================================
# RETRY
# =============================================================================

def _sleep_backoff(attempt: int) -> None:
    # exponential with jitter, capped
    base = min(2 ** attempt, 20)
    time.sleep(base + random.random())

def _chat_with_retry(**kwargs):
    last_error: Optional[Exception] = None
    for attempt in range(6):
        try:
            return client.chat.completions.create(**kwargs)
        except (InternalServerError, RateLimitError, APITimeoutError) as e:
            last_error = e
            _sleep_backoff(attempt)
    # if we got here, last_error is set
    raise last_error  # type: ignore[misc]


# =============================================================================
# JSON HELPERS
# =============================================================================

def _safe_json_load(s: str) -> Dict[str, Any]:
    s = (s or "").strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        pass

    # Attempt extract first {...}
    try:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(s[start : end + 1])
    except Exception:
        pass

    return {}

def _clean_str(x: Any) -> str:
    s = (str(x) if x is not None else "").strip()
    if s in ("...", "…"):
        return ""
    return s

def _ensure_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []

def _ensure_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}

def _coerce_int(x: Any, default: int = 0) -> int:
    try:
        if x is None or isinstance(x, bool):
            return default
        if isinstance(x, (int, float)):
            return int(x)
        return int(float(str(x).replace(",", ".")))
    except Exception:
        return default

def _coerce_float(x: Any, default: float = 0.0) -> float:
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
    out: List[str] = []
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


# =============================================================================
# QUICK REJECT (from file 1)
# =============================================================================

BLOCK_PATTERNS = [
    r"\brésultat\b", r"\bscore\b", r"\bmatch\b", r"\bligue\b", r"\bbut\b",
    r"\bélection\b", r"\bprésident\b", r"\bministre\b", r"\bguerre\b", r"\battaque\b",
    r"\bmétéo\b", r"\btrafic\b", r"\bgrève\b",
    r"\baccident\b", r"\bmort\b", r"\bdécès\b",
    r"\bfilm\b", r"\bsérie\b", r"\bacteur\b", r"\bactrice\b",
    r"\bconcert\b", r"\bfestival\b",
]
BRAND_BLOCKLIST = ["iphone", "samsung", "ps5", "playstation", "xbox", "netflix", "disney", "tesla", "apple", "meta"]

_block_re = re.compile("|".join(BLOCK_PATTERNS), re.IGNORECASE)

def quick_reject(term: str) -> bool:
    t = (term or "").strip().lower()
    if not t:
        return True
    if len(t) < 3:
        return True
    if _block_re.search(t):
        return True
    if any(b in t for b in BRAND_BLOCKLIST):
        return True
    return False


# =============================================================================
# RESPONSE_FORMAT SUPPORT (best effort)
# =============================================================================

def _chat_json_best_effort(
    *,
    model: str,
    temperature: float,
    messages: List[Dict[str, str]],
) -> str:
    """
    Tries to force JSON via response_format when supported.
    Falls back to plain call if the client/model doesn't accept it.
    """
    # Attempt JSON mode
    try:
        resp = _chat_with_retry(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=messages,
        )
        return (resp.choices[0].message.content or "").strip()
    except TypeError:
        # response_format not supported by this client/env
        pass
    except Exception:
        # if model doesn't support json_object, it may throw a request error
        # we try without response_format as fallback
        pass

    resp = _chat_with_retry(
        model=model,
        temperature=temperature,
        messages=messages,
    )
    return (resp.choices[0].message.content or "").strip()


# =============================================================================
# AI HELPERS
# =============================================================================

def extract_product_name(caption: str, geo: str = "FR") -> str:
    caption = (caption or "").strip()
    if not caption:
        return ""

    txt = _chat_json_best_effort(
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

    if txt.upper().startswith("RIEN"):
        return ""
    # keep it short
    return txt[:80]


def classify_sellability(term: str, geo: str = "FR") -> Dict[str, Any]:
    """
    Returns {sellable: bool, score: 0-100, reason: str}
    Inspired by file 1 (strict + score).
    """
    term = (term or "").strip()
    if not term:
        return {"sellable": False, "score": 0, "reason": "empty"}
    if quick_reject(term):
        return {"sellable": False, "score": 0, "reason": "quick_reject"}

    prompt = {
        "term": term,
        "market": geo,
        "rules": [
            "sellable=true seulement si c'est un produit e-commerce concret vendable (objet/accessoire).",
            "sellable=false si actu, politique, sport, people, marque, événement, service ou trop vague.",
            "score = vendabilité 0-100 (100 = très vendable, démontrable en vidéo, achat impulsif).",
            "Sois strict. Si doute, sellable=false."
        ],
        "output_json": {"sellable": True, "score": 75, "reason": "string"},
    }

    txt = _chat_json_best_effort(
        model=_model(),
        temperature=0,
        messages=[
            {"role": "system", "content": "Réponds uniquement en JSON valide."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )

    data = _safe_json_load(txt)
    sellable = bool(data.get("sellable", False))
    score = _coerce_int(data.get("score", 0), 0)
    score = int(_clamp(score, 0, 100))
    reason = _clean_str(data.get("reason", "")) or "ok"

    if not sellable or score <= 0:
        return {"sellable": False, "score": 0, "reason": reason}
    return {"sellable": True, "score": score, "reason": reason}


def is_sellable_product(term: str, geo: str = "FR") -> bool:
    # Compatibility wrapper
    return bool(classify_sellability(term, geo).get("sellable", False))


# =============================================================================
# ANALYSIS SCHEMA (from file 1)
# =============================================================================

ANALYSIS_SCHEMA: Dict[str, Any] = {
    "positioning": {"main_promise": "", "target_customer": "", "problem_solved": "", "why_now": ""},
    "angles": {
        "hooks": ["", "", ""],
        "objections": [{"objection": "", "response": ""}],
        "ugc_script": {"script": "", "duration_seconds": 20}
    },
    "risks": [{"type": "", "level": "low", "note": ""}],
    "recommendations": {
        "price_range": {"min": 0, "max": 0, "currency": "EUR"},
        "channels": ["TikTok Ads"],
        "upsells": [""]
    },
    "confidence": {"score": 0, "reasons": [""]}
}


# =============================================================================
# SCHEMA ENFORCER + POSTPROCESS
# =============================================================================

def _merge_schema(schema: Any, data: Any) -> Any:
    """
    Forces 'data' to match 'schema' shape (keys/types),
    filling missing values with defaults from schema.
    """
    if isinstance(schema, dict):
        out: Dict[str, Any] = {}
        d = _ensure_dict(data)
        for k, v in schema.items():
            out[k] = _merge_schema(v, d.get(k))
        return out

    if isinstance(schema, list):
        item_schema = schema[0] if schema else ""
        arr = _ensure_list(data)
        if not arr:
            return schema
        return [_merge_schema(item_schema, x) for x in arr]

    # primitives
    if isinstance(schema, int):
        return _coerce_int(data, schema)
    if isinstance(schema, float):
        return _coerce_float(data, schema)
    return _clean_str(data)

def _postprocess_analysis(a: Dict[str, Any]) -> Dict[str, Any]:
    out = _merge_schema(ANALYSIS_SCHEMA, a)

    # hooks: 3 max, unique, non-empty preferred
    hooks = _uniq_keep_order([_clean_str(x) for x in _ensure_list(out["angles"].get("hooks"))])
    hooks = (hooks + ["", "", ""])[:3]
    out["angles"]["hooks"] = hooks

    # objections: 1-3
    obj = _ensure_list(out["angles"].get("objections"))
    cleaned_obj: List[Dict[str, str]] = []
    for it in obj[:3]:
        d = _ensure_dict(it)
        objection = _clean_str(d.get("objection"))
        response = _clean_str(d.get("response"))
        if objection or response:
            cleaned_obj.append({"objection": objection, "response": response})
    if not cleaned_obj:
        cleaned_obj = [{"objection": "", "response": ""}]
    out["angles"]["objections"] = cleaned_obj

    # ugc duration clamp
    dur = _coerce_int(out["angles"]["ugc_script"].get("duration_seconds"), 20)
    out["angles"]["ugc_script"]["duration_seconds"] = int(_clamp(dur, 5, 60))

    # risks: at least 1, normalize level
    risks = _ensure_list(out.get("risks"))
    if not risks:
        risks = [{"type": "unknown", "level": "low", "note": ""}]
    norm: List[Dict[str, str]] = []
    for r in risks:
        d = _ensure_dict(r)
        lvl = _clean_str(d.get("level")).lower()
        if lvl not in ("low", "medium", "high"):
            lvl = "low"
        norm.append({
            "type": _clean_str(d.get("type")),
            "level": lvl,
            "note": _clean_str(d.get("note")),
        })
    out["risks"] = norm[:5]

    # confidence score 1-10 (or 0 if missing)
    cs = _coerce_int(out["confidence"].get("score"), 0)
    out["confidence"]["score"] = int(_clamp(cs, 1, 10)) if cs else 0
    out["confidence"]["reasons"] = _uniq_keep_order([_clean_str(x) for x in _ensure_list(out["confidence"].get("reasons"))]) or [""]

    # price range min/max
    pr = out["recommendations"]["price_range"]
    mn = _coerce_int(pr.get("min"), 0)
    mx = _coerce_int(pr.get("max"), 0)
    mn = int(_clamp(mn, 0, 9999))
    mx = int(_clamp(mx, 0, 9999))
    if mn and mx and mn > mx:
        mn, mx = mx, mn
    pr["min"], pr["max"] = mn, mx
    pr["currency"] = _clean_str(pr.get("currency")) or "EUR"

    # channels/upsells unique
    out["recommendations"]["channels"] = _uniq_keep_order([_clean_str(x) for x in _ensure_list(out["recommendations"].get("channels"))]) or ["TikTok Ads"]
    out["recommendations"]["upsells"] = _uniq_keep_order([_clean_str(x) for x in _ensure_list(out["recommendations"].get("upsells"))])

    # positioning strings cleaned
    pos = out.get("positioning", {})
    out["positioning"] = {
        "main_promise": _clean_str(pos.get("main_promise")),
        "target_customer": _clean_str(pos.get("target_customer")),
        "problem_solved": _clean_str(pos.get("problem_solved")),
        "why_now": _clean_str(pos.get("why_now")),
    }

    return out

def _analysis_is_too_empty(a: Dict[str, Any]) -> bool:
    """
    Sanity check to avoid "schema-filled emptiness".
    If the model returns almost nothing meaningful, we try repair/retry.
    """
    a = _postprocess_analysis(a)
    hooks = [h for h in _ensure_list(a["angles"].get("hooks")) if _clean_str(h)]
    script = _clean_str(_ensure_dict(a["angles"].get("ugc_script")).get("script"))
    main_promise = _clean_str(_ensure_dict(a.get("positioning")).get("main_promise"))
    # if everything core is empty, it's not acceptable
    return (len(hooks) == 0) and (not script) and (not main_promise)


# =============================================================================
# FALLBACK (used only after failed parse/repair)
# =============================================================================

def _default_analysis(title: str) -> Dict[str, Any]:
    base = {
        "positioning": {
            "main_promise": "Résultat visible rapidement avec un usage simple.",
            "target_customer": "Public 18-45 acheteurs impulsifs.",
            "problem_solved": "Résout un irritant du quotidien.",
            "why_now": "Les formats UGC courts boostent les produits démontrables.",
        },
        "angles": {
            "hooks": [
                f"Tu fais encore [problème] comme ça ? {title} change tout.",
                f"Le avant/après de {title} en 5 secondes (dingue).",
                f"Si tu en as marre de [douleur], {title} peut t’aider.",
            ],
            "objections": [
                {"objection": "Ça a l’air gadget", "response": "On montre la démo avant/après en 5 secondes."},
                {"objection": "Je ne sais pas si ça marche", "response": "Preuve sociale + vidéo UGC simple et claire."},
            ],
            "ugc_script": {"script": f"J’avais [problème]… puis j’ai testé {title}. Regarde la différence.", "duration_seconds": 20},
        },
        "risks": [{"type": "concurrence", "level": "medium", "note": "Concurrence possible sur ce type de produit."}],
        "recommendations": {
            "price_range": {"min": 19, "max": 49, "currency": "EUR"},
            "channels": ["TikTok Ads", "UGC", "Retargeting"],
            "upsells": ["Accessoires", "Bundle"],
        },
        "confidence": {"score": 6, "reasons": ["Signal TikTok observé", "Produit simple à comprendre en vidéo"]},
    }
    return _postprocess_analysis(base)


# =============================================================================
# JSON REPAIR (2nd chance before fallback)
# =============================================================================

def _repair_to_schema(raw_text: str, product_payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    prompt = {
        "task": "Convertis la sortie suivante en JSON VALIDE qui respecte EXACTEMENT le schéma (mêmes clés).",
        "market": geo,
        "schema": ANALYSIS_SCHEMA,
        "product": product_payload,
        "raw_output": raw_text,
        "rules": [
            "Ne retourne que du JSON valide.",
            "Garde les mêmes clés que le schéma, pas de clés en plus.",
            "Remplis avec du contenu concret et spécifique au produit si possible.",
        ],
    }

    txt = _chat_json_best_effort(
        model=_model(),
        temperature=0,
        messages=[
            {"role": "system", "content": "Réponds uniquement en JSON valide."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )

    data = _safe_json_load(txt)
    if not data:
        return {}
    return data


# =============================================================================
# GENERATE ANALYSIS (strict + schema + repair + minimal fallback)
# =============================================================================

def generate_analysis(product_payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    """
    This is the "file 2 but as it should work" version:
    - forces schema
    - tries JSON mode when possible
    - does one repair pass before fallback
    - avoids falling back "by default"
    """
    title = _clean_str(product_payload.get("title") or product_payload.get("name") or "")
    if not title:
        title = "ce produit"

    prompt = {
        "market": geo,
        "instructions": [
            "Tu es un expert e-commerce. Réponds uniquement en JSON valide.",
            "Tu dois respecter exactement le schéma fourni (mêmes clés).",
            "Hooks style Minea: courts, punchy, orientés douleur/bénéfice.",
            "Objections: 1 à 3 objections max + réponses courtes.",
            "Risks: au moins 1 risque avec level low|medium|high.",
            "Confidence.score: 1-10, cohérent avec les signaux (Trends/TikTok/Pinterest).",
            "Price_range: réaliste en EUR pour test en publicité."
        ],
        "schema": ANALYSIS_SCHEMA,
        "product": product_payload,
    }

    # 1st attempt
    txt = _chat_json_best_effort(
        model=_model(),
        temperature=0.4,
        messages=[
            {"role": "system", "content": "Réponds uniquement en JSON valide."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )

    data = _safe_json_load(txt)

    # If parse failed OR data is essentially empty -> repair attempt
    if not data or _analysis_is_too_empty(data):
        repaired = _repair_to_schema(txt, product_payload, geo)
        if repaired and not _analysis_is_too_empty(repaired):
            return _postprocess_analysis(repaired)

        # Last resort: fallback
        return _default_analysis(title)

    # Parsed OK and not empty -> postprocess
    return _postprocess_analysis(data)


# =============================================================================
# OPTIONAL: PIPELINE HELPER (caption -> product -> sellability -> analysis)
# =============================================================================

def analyze_from_caption(caption: str, geo: str = "FR") -> Dict[str, Any]:
    """
    Convenience: takes a TikTok caption, extracts product, checks sellability (strict),
    returns analysis if sellable.
    """
    name = extract_product_name(caption, geo)
    if not name:
        return {"ok": False, "reason": "no_product_found"}

    sell = classify_sellability(name, geo)
    if not sell["sellable"]:
        return {"ok": False, "reason": "not_sellable", "sellability": sell, "product": name}

    payload = {"title": name, "source_caption": caption}
    analysis = generate_analysis(payload, geo)

    return {"ok": True, "product": name, "sellability": sell, "analysis": analysis}