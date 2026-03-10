from __future__ import annotations

import os
import json
import time
import random
import re
import unicodedata
from typing import Any, Dict, List, Optional

from openai import OpenAI, InternalServerError, RateLimitError, APITimeoutError

# =============================================================================
# CONFIG
# =============================================================================

client = OpenAI(api_key=(os.environ.get("OPENAI_API_KEY") or "").strip())


def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"


ALLOWED_CATEGORIES = [
    "maison",
    "beauté",
    "cuisine",
    "fitness",
    "animaux",
    "auto",
    "accessoires",
    "rangement",
    "jardin",
]


# =============================================================================
# RETRY
# =============================================================================

def _sleep_backoff(attempt: int) -> None:
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
    raise last_error  # type: ignore[misc]


# =============================================================================
# BASIC HELPERS
# =============================================================================

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


def _clean_str(x: Any) -> str:
    s = (str(x) if x is not None else "").strip()
    if s in ("...", "…", "null", "None"):
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


def _slugify(text: str) -> str:
    text = _clean_str(text).lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:120]


def _contains_french_markers(text: str) -> bool:
    t = f" {_clean_str(text).lower()} "
    markers = [
        " le ", " la ", " les ", " de ", " du ", " des ", " pour ", " avec ",
        " miroir ", " brosse ", " organisateur ", " support ", " rangement ",
        " décoratif ", " mural ", " cuisine ", " voiture ", " chien ", " chat ",
    ]
    return any(m in t for m in markers)


# =============================================================================
# QUICK REJECT
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
# CHAT HELPERS
# =============================================================================

def _extract_content(resp: Any) -> str:
    try:
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""


def _chat_text(
    *,
    model: str,
    temperature: float,
    messages: List[Dict[str, str]],
) -> str:
    resp = _chat_with_retry(
        model=model,
        temperature=temperature,
        messages=messages,
    )
    return _extract_content(resp)


def _chat_json_best_effort(
    *,
    model: str,
    temperature: float,
    messages: List[Dict[str, str]],
    json_schema: Optional[Dict[str, Any]] = None,
) -> str:
    if json_schema:
        try:
            resp = _chat_with_retry(
                model=model,
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": json_schema,
                },
                messages=messages,
            )
            return _extract_content(resp)
        except TypeError:
            pass
        except Exception:
            pass

    try:
        resp = _chat_with_retry(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=messages,
        )
        return _extract_content(resp)
    except TypeError:
        pass
    except Exception:
        pass

    resp = _chat_with_retry(
        model=model,
        temperature=temperature,
        messages=messages,
    )
    return _extract_content(resp)


# =============================================================================
# SCHEMAS
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

POSITIONING_JSON_SCHEMA = {
    "name": "positioning_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "main_promise": {"type": "string"},
            "target_customer": {"type": "string"},
            "problem_solved": {"type": "string"},
            "why_now": {"type": "string"},
        },
        "required": ["main_promise", "target_customer", "problem_solved", "why_now"],
    },
}

HOOKS_JSON_SCHEMA = {
    "name": "hooks_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "hooks": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3,
            }
        },
        "required": ["hooks"],
    },
}

OBJECTIONS_JSON_SCHEMA = {
    "name": "objections_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "objections": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "objection": {"type": "string"},
                        "response": {"type": "string"},
                    },
                    "required": ["objection", "response"],
                },
            }
        },
        "required": ["objections"],
    },
}

UGC_JSON_SCHEMA = {
    "name": "ugc_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "script": {"type": "string"},
            "duration_seconds": {"type": "integer"},
        },
        "required": ["script", "duration_seconds"],
    },
}

RISKS_JSON_SCHEMA = {
    "name": "risks_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "risks": {
                "type": "array",
                "minItems": 1,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "type": {"type": "string"},
                        "level": {"type": "string", "enum": ["low", "medium", "high"]},
                        "note": {"type": "string"},
                    },
                    "required": ["type", "level", "note"],
                },
            }
        },
        "required": ["risks"],
    },
}

RECOMMENDATIONS_JSON_SCHEMA = {
    "name": "recommendations_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "price_range": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "min": {"type": "integer"},
                    "max": {"type": "integer"},
                    "currency": {"type": "string"},
                },
                "required": ["min", "max", "currency"],
            },
            "channels": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 5,
            },
            "upsells": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 0,
                "maxItems": 5,
            },
        },
        "required": ["price_range", "channels", "upsells"],
    },
}

CONFIDENCE_JSON_SCHEMA = {
    "name": "confidence_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "score": {"type": "integer"},
            "reasons": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 4,
            },
        },
        "required": ["score", "reasons"],
    },
}

SUMMARY_JSON_SCHEMA = {
    "name": "summary_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
        },
        "required": ["summary"],
    },
}

CATEGORY_JSON_SCHEMA = {
    "name": "category_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "category": {"type": "string", "enum": ALLOWED_CATEGORIES},
        },
        "required": ["category"],
    },
}

TAGS_JSON_SCHEMA = {
    "name": "tags_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 5,
            }
        },
        "required": ["tags"],
    },
}


# =============================================================================
# SCHEMA ENFORCER + POSTPROCESS
# =============================================================================

def _merge_schema(schema: Any, data: Any) -> Any:
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

    if isinstance(schema, int):
        return _coerce_int(data, schema)
    if isinstance(schema, float):
        return _coerce_float(data, schema)
    return _clean_str(data)


def _postprocess_analysis(a: Dict[str, Any]) -> Dict[str, Any]:
    out = _merge_schema(ANALYSIS_SCHEMA, a)

    hooks = _uniq_keep_order([_clean_str(x) for x in _ensure_list(out["angles"].get("hooks"))])
    hooks = (hooks + ["", "", ""])[:3]
    out["angles"]["hooks"] = hooks

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

    dur = _coerce_int(out["angles"]["ugc_script"].get("duration_seconds"), 20)
    out["angles"]["ugc_script"]["duration_seconds"] = int(_clamp(dur, 8, 45))
    out["angles"]["ugc_script"]["script"] = _clean_str(out["angles"]["ugc_script"].get("script"))

    risks = _ensure_list(out.get("risks"))
    if not risks:
        risks = [{"type": "positionnement", "level": "low", "note": ""}]
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

    cs = _coerce_int(out["confidence"].get("score"), 0)
    out["confidence"]["score"] = int(_clamp(cs, 1, 10)) if cs else 6
    out["confidence"]["reasons"] = _uniq_keep_order(
        [_clean_str(x) for x in _ensure_list(out["confidence"].get("reasons"))]
    ) or ["Confiance moyenne par défaut."]

    pr = out["recommendations"]["price_range"]
    mn = _coerce_int(pr.get("min"), 0)
    mx = _coerce_int(pr.get("max"), 0)
    mn = int(_clamp(mn, 0, 9999))
    mx = int(_clamp(mx, 0, 9999))
    if mn and mx and mn > mx:
        mn, mx = mx, mn
    if mn == 0 and mx == 0:
        mn, mx = 19, 49
    pr["min"], pr["max"] = mn, mx
    pr["currency"] = _clean_str(pr.get("currency")) or "EUR"

    out["recommendations"]["channels"] = _uniq_keep_order(
        [_clean_str(x) for x in _ensure_list(out["recommendations"].get("channels"))]
    ) or ["TikTok Ads"]

    out["recommendations"]["upsells"] = _uniq_keep_order(
        [_clean_str(x) for x in _ensure_list(out["recommendations"].get("upsells"))]
    )

    pos = out.get("positioning", {})
    out["positioning"] = {
        "main_promise": _clean_str(pos.get("main_promise")),
        "target_customer": _clean_str(pos.get("target_customer")),
        "problem_solved": _clean_str(pos.get("problem_solved")),
        "why_now": _clean_str(pos.get("why_now")),
    }

    return out


# =============================================================================
# PRODUCT CONTEXT
# =============================================================================

def _build_product_context(product_payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    signals = _ensure_dict(product_payload.get("signals"))
    score_breakdown = _ensure_dict(product_payload.get("score_breakdown"))

    context = {
        "market": geo,
        "title": _clean_str(product_payload.get("title") or product_payload.get("name")),
        "category": _clean_str(product_payload.get("category")),
        "tags": _ensure_list(product_payload.get("tags")),
        "summary": _clean_str(product_payload.get("summary")),
        "source_caption": _clean_str(product_payload.get("source_caption") or product_payload.get("caption")),
        "sources": _ensure_list(product_payload.get("sources")),
        "signals": signals,
        "score": _coerce_int(product_payload.get("score"), 0),
        "score_breakdown": score_breakdown,
    }

    if not context["title"]:
        context["title"] = "ce produit"

    return context


# =============================================================================
# AI HELPERS
# =============================================================================

def _ensure_french_title(title: str, geo: str = "FR") -> str:
    title = _clean_str(title)
    if not title:
        return ""

    if _contains_french_markers(title):
        return title[:80]

    txt = _chat_text(
        model=_model(),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu reçois un nom de produit e-commerce. "
                    "S'il est en anglais ou mélangé, traduis-le et normalise-le en français naturel. "
                    "Garde un nom court, clair, vendable, de 2 à 6 mots. "
                    "Réponds uniquement avec le nom du produit, sans phrase, sans JSON, sans guillemets."
                ),
            },
            {"role": "user", "content": f"Marché: {geo}\nNom produit: {title}"},
        ],
    )

    txt = _clean_str(txt).strip('"').strip("'")
    txt = re.sub(r"\s+", " ", txt)
    return txt[:80].strip(" .,-") or title[:80]


def _normalize_product_title(title: str, geo: str = "FR") -> str:
    title = _clean_str(title)
    if not title:
        return ""

    txt = _chat_text(
        model=_model(),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Normalise ce nom de produit pour une base e-commerce française. "
                    "Le résultat doit être en français naturel, court, clair, propre et vendable. "
                    "Évite l'ordre maladroit des mots, les répétitions et les mots inutiles. "
                    "Réponds uniquement avec le nom final, sans phrase, sans JSON, sans guillemets. "
                    "2 à 6 mots maximum."
                ),
            },
            {"role": "user", "content": f"Marché: {geo}\nNom produit: {title}"},
        ],
    )

    txt = _clean_str(txt).strip('"').strip("'")
    txt = re.sub(r"\s+", " ", txt)
    txt = txt[:80].strip(" .,-")
    return txt or title[:80]


def extract_product_name(caption: str, geo: str = "FR") -> str:
    caption = (caption or "").strip()
    if not caption:
        return ""

    txt = _chat_text(
        model=_model(),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extrait UN SEUL nom de produit e-commerce concret depuis une caption TikTok. "
                    "Réponds uniquement par le nom du produit, sans JSON, sans phrase, sans guillemets. "
                    "2 à 6 mots maximum. Si aucun produit clair : RIEN"
                ),
            },
            {"role": "user", "content": f"Caption: {caption}\nMarché: {geo}"},
        ],
    )

    txt = txt.strip().strip('"').strip("'").strip()
    if txt.upper() == "RIEN":
        return ""

    txt = re.sub(r"\s+", " ", txt)
    txt = txt[:80].strip(" .,-")

    if quick_reject(txt):
        return ""

    txt = _ensure_french_title(txt, geo=geo)
    txt = _normalize_product_title(txt, geo=geo)

    if quick_reject(txt):
        return ""

    return txt


def classify_sellability(term: str, geo: str = "FR") -> Dict[str, Any]:
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
    }

    txt = _chat_json_best_effort(
        model=_model(),
        temperature=0,
        json_schema={
            "name": "sellability_schema",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "sellable": {"type": "boolean"},
                    "score": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["sellable", "score", "reason"],
            },
        },
        messages=[
            {"role": "system", "content": "Réponds uniquement en JSON valide."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )

    data = _safe_json_load(txt)
    sellable = bool(data.get("sellable", False))
    score = int(_clamp(_coerce_int(data.get("score", 0), 0), 0, 100))
    reason = _clean_str(data.get("reason")) or "ok"

    if not sellable or score <= 0:
        return {"sellable": False, "score": 0, "reason": reason}
    return {"sellable": True, "score": score, "reason": reason}


def is_sellable_product(term: str, geo: str = "FR") -> bool:
    return bool(classify_sellability(term, geo).get("sellable", False))


# =============================================================================
# BLOCK GENERATION HELPERS
# =============================================================================

def _call_block_json(
    *,
    schema: Dict[str, Any],
    system_prompt: str,
    user_payload: Dict[str, Any],
    temperature: float = 0.1,
    retries: int = 3,
) -> Dict[str, Any]:
    last: Dict[str, Any] = {}
    for _ in range(retries):
        txt = _chat_json_best_effort(
            model=_model(),
            temperature=temperature,
            json_schema=schema,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )
        data = _safe_json_load(txt)
        if data:
            last = data
            if any(_clean_str(v) for v in data.values() if not isinstance(v, (dict, list))):
                return data
            if any(isinstance(v, (dict, list)) for v in data.values()):
                return data
    return last


def _generate_category(context: Dict[str, Any]) -> str:
    existing = _clean_str(context.get("category"))
    if existing in ALLOWED_CATEGORIES:
        return existing

    payload = {
        "task": "Classifie le produit dans UNE catégorie parmi la liste autorisée.",
        "allowed_categories": ALLOWED_CATEGORIES,
        "rules": [
            "Choisis uniquement une catégorie dans la liste",
            "Ne crée pas de nouvelle catégorie",
            "Réponds uniquement avec une catégorie autorisée"
        ],
        "product_context": context,
    }

    data = _call_block_json(
        schema=CATEGORY_JSON_SCHEMA,
        system_prompt="Tu classes un produit e-commerce. Réponds uniquement en JSON.",
        user_payload=payload,
        temperature=0,
    )
    category = _clean_str(data.get("category"))
    if category not in ALLOWED_CATEGORIES:
        category = "accessoires"
    return category


def _generate_tags(context: Dict[str, Any]) -> List[str]:
    existing = [_clean_str(x) for x in _ensure_list(context.get("tags")) if _clean_str(x)]
    if len(existing) >= 2:
        return _uniq_keep_order(existing)[:5]

    payload = {
        "task": "Génère 2 à 5 tags e-commerce utiles et concrets en français.",
        "rules": [
            "Tags courts",
            "Pas de hashtags",
            "Pas de mots trop génériques",
            "Liés au produit, à son usage ou à son univers"
        ],
        "product_context": context,
    }

    data = _call_block_json(
        schema=TAGS_JSON_SCHEMA,
        system_prompt="Tu génères des tags e-commerce. Réponds uniquement en JSON.",
        user_payload=payload,
        temperature=0.1,
    )
    tags = _uniq_keep_order([_clean_str(x) for x in _ensure_list(data.get("tags"))])
    if len(tags) >= 2:
        return tags[:5]

    title_words = [w for w in re.split(r"[\s\-/_,;:]+", _clean_str(context.get("title")).lower()) if len(w) >= 3]
    category = _clean_str(context.get("category"))
    heuristic = _uniq_keep_order(title_words[:3] + ([category] if category else []))
    return heuristic[:5] or ["tendance", "produit"]


def _generate_positioning(context: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "task": "Génère un positionnement e-commerce spécifique au produit.",
        "rules": [
            "Concret, spécifique, sans phrases creuses",
            "Marché FR",
            "Pensé pour publicité courte et produit démontrable",
        ],
        "product_context": context,
    }

    data = _call_block_json(
        schema=POSITIONING_JSON_SCHEMA,
        system_prompt=(
            "Tu es expert e-commerce DTC. Réponds uniquement en JSON. "
            "Sois spécifique au produit et à son usage. Évite les formulations génériques."
        ),
        user_payload=payload,
        temperature=0.1,
    )

    out = {
        "main_promise": _clean_str(data.get("main_promise")),
        "target_customer": _clean_str(data.get("target_customer")),
        "problem_solved": _clean_str(data.get("problem_solved")),
        "why_now": _clean_str(data.get("why_now")),
    }

    title = _clean_str(context.get("title")) or "ce produit"
    category = _clean_str(context.get("category")) or "produit du quotidien"

    if not out["main_promise"]:
        out["main_promise"] = f"{title} apporte une amélioration visible et simple à comprendre."
    if not out["target_customer"]:
        out["target_customer"] = f"Personnes intéressées par {category} et prêtes à tester un produit utile."
    if not out["problem_solved"]:
        out["problem_solved"] = f"Un usage du quotidien mal optimisé que {title} rend plus simple ou plus agréable."
    if not out["why_now"]:
        out["why_now"] = f"{title} se prête bien à la démonstration courte en vidéo et au format UGC."

    return out


def _generate_hooks(context: Dict[str, Any], positioning: Dict[str, Any]) -> List[str]:
    payload = {
        "task": "Génère 3 hooks publicitaires courts style TikTok/Minea.",
        "rules": [
            "Punchy, concrets, compréhensibles",
            "Pas de promesse médicale",
            "Pas de placeholders comme [problème]",
            "Spécifiques au produit"
        ],
        "product_context": context,
        "positioning": positioning,
    }

    data = _call_block_json(
        schema=HOOKS_JSON_SCHEMA,
        system_prompt=(
            "Tu écris 3 hooks e-commerce. Réponds uniquement en JSON. "
            "Les hooks doivent être spécifiques au produit, courts et vendables."
        ),
        user_payload=payload,
        temperature=0.2,
    )

    hooks = _uniq_keep_order([_clean_str(x) for x in _ensure_list(data.get("hooks"))])[:3]
    title = _clean_str(context.get("title")) or "ce produit"

    while len(hooks) < 3:
        idx = len(hooks) + 1
        if idx == 1:
            hooks.append(f"Je ne pensais pas que {title} ferait une vraie différence avant de le tester.")
        elif idx == 2:
            hooks.append(f"Le type de produit qu’on comprend vraiment seulement en voyant {title} en action.")
        else:
            hooks.append(f"Pourquoi tout le monde parle de {title} en vidéo courte ?")
    return hooks[:3]


def _generate_objections(context: Dict[str, Any], positioning: Dict[str, Any]) -> List[Dict[str, str]]:
    payload = {
        "task": "Génère 1 à 3 objections réalistes et leurs réponses.",
        "rules": [
            "Objections crédibles avant achat",
            "Réponses courtes, concrètes, orientées conversion",
            "Spécifiques au produit"
        ],
        "product_context": context,
        "positioning": positioning,
    }

    data = _call_block_json(
        schema=OBJECTIONS_JSON_SCHEMA,
        system_prompt="Tu génères des objections e-commerce et leurs réponses. Réponds uniquement en JSON.",
        user_payload=payload,
        temperature=0.1,
    )

    out: List[Dict[str, str]] = []
    for it in _ensure_list(data.get("objections"))[:3]:
        d = _ensure_dict(it)
        objection = _clean_str(d.get("objection"))
        response = _clean_str(d.get("response"))
        if objection or response:
            out.append({"objection": objection, "response": response})

    title = _clean_str(context.get("title")) or "ce produit"
    if not out:
        out = [
            {
                "objection": f"{title} a l'air gadget",
                "response": "La démonstration en situation réelle doit montrer immédiatement l'utilité du produit."
            }
        ]
    return out[:3]


def _generate_ugc_script(context: Dict[str, Any], positioning: Dict[str, Any], hooks: List[str]) -> Dict[str, Any]:
    payload = {
        "task": "Génère un script UGC court de 15 à 30 secondes.",
        "rules": [
            "Français naturel",
            "Début problème ou surprise",
            "Milieu démonstration produit",
            "Fin bénéfice clair",
            "Une seule personne peut le lire face caméra"
        ],
        "product_context": context,
        "positioning": positioning,
        "hooks": hooks,
    }

    data = _call_block_json(
        schema=UGC_JSON_SCHEMA,
        system_prompt="Tu écris un script UGC e-commerce. Réponds uniquement en JSON.",
        user_payload=payload,
        temperature=0.2,
    )

    script = _clean_str(data.get("script"))
    duration = int(_clamp(_coerce_int(data.get("duration_seconds"), 20), 8, 45))
    title = _clean_str(context.get("title")) or "ce produit"

    if not script:
        script = (
            f"Je pensais vraiment que {title} serait un gadget. "
            f"Puis je l'ai testé en condition réelle, et on comprend tout de suite l'intérêt. "
            f"Le gain se voit rapidement, c'est simple à utiliser, et maintenant je m'en sers sans réfléchir."
        )

    return {"script": script, "duration_seconds": duration}


def _generate_risks(context: Dict[str, Any], positioning: Dict[str, Any]) -> List[Dict[str, str]]:
    payload = {
        "task": "Génère 1 à 3 risques business ou marketing réalistes.",
        "rules": [
            "Risques e-commerce, créa, concurrence, perception, pricing ou qualité perçue",
            "Niveaux uniquement low, medium ou high",
            "Notes courtes et actionnables"
        ],
        "product_context": context,
        "positioning": positioning,
    }

    data = _call_block_json(
        schema=RISKS_JSON_SCHEMA,
        system_prompt="Tu identifies des risques e-commerce. Réponds uniquement en JSON.",
        user_payload=payload,
        temperature=0.1,
    )

    risks: List[Dict[str, str]] = []
    for it in _ensure_list(data.get("risks"))[:5]:
        d = _ensure_dict(it)
        lvl = _clean_str(d.get("level")).lower()
        if lvl not in ("low", "medium", "high"):
            lvl = "low"
        risks.append({
            "type": _clean_str(d.get("type")),
            "level": lvl,
            "note": _clean_str(d.get("note")),
        })

    if not risks:
        risks = [{
            "type": "compréhension produit",
            "level": "medium",
            "note": "Le produit doit être montré clairement en situation réelle pour éviter l'effet gadget."
        }]

    return risks[:5]


def _generate_recommendations(context: Dict[str, Any], positioning: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "task": "Génère des recommandations marketing réalistes pour lancer/tester le produit.",
        "rules": [
            "Prix en EUR",
            "Canaux plausibles",
            "Upsells cohérents avec le produit",
            "Pas de recommandations absurdes ou trop génériques"
        ],
        "product_context": context,
        "positioning": positioning,
    }

    data = _call_block_json(
        schema=RECOMMENDATIONS_JSON_SCHEMA,
        system_prompt="Tu génères des recommandations e-commerce. Réponds uniquement en JSON.",
        user_payload=payload,
        temperature=0.1,
    )

    pr = _ensure_dict(data.get("price_range"))
    mn = int(_clamp(_coerce_int(pr.get("min"), 19), 0, 9999))
    mx = int(_clamp(_coerce_int(pr.get("max"), 49), 0, 9999))
    if mn and mx and mn > mx:
        mn, mx = mx, mn
    if mn == 0 and mx == 0:
        mn, mx = 19, 49

    channels = _uniq_keep_order([_clean_str(x) for x in _ensure_list(data.get("channels"))]) or ["TikTok Ads"]
    upsells = _uniq_keep_order([_clean_str(x) for x in _ensure_list(data.get("upsells"))])

    return {
        "price_range": {
            "min": mn,
            "max": mx,
            "currency": _clean_str(pr.get("currency")) or "EUR",
        },
        "channels": channels[:5],
        "upsells": upsells[:5],
    }


def _generate_confidence(
    context: Dict[str, Any],
    positioning: Dict[str, Any],
    hooks: List[str],
    objections: List[Dict[str, str]],
    ugc_script: Dict[str, Any],
    risks: List[Dict[str, str]],
    recommendations: Dict[str, Any],
) -> Dict[str, Any]:
    payload = {
        "task": "Estime une confiance globale 1-10 sur le potentiel marketing du produit.",
        "rules": [
            "Base-toi sur le contexte produit et les signaux disponibles",
            "Donne 1 à 4 raisons courtes",
            "Ne surévalue pas sans signal"
        ],
        "product_context": context,
        "draft_analysis": {
            "positioning": positioning,
            "hooks": hooks,
            "objections": objections,
            "ugc_script": ugc_script,
            "risks": risks,
            "recommendations": recommendations,
        },
    }

    data = _call_block_json(
        schema=CONFIDENCE_JSON_SCHEMA,
        system_prompt="Tu estimes une confiance marketing. Réponds uniquement en JSON.",
        user_payload=payload,
        temperature=0,
    )

    score = int(_clamp(_coerce_int(data.get("score"), 6), 1, 10))
    reasons = _uniq_keep_order([_clean_str(x) for x in _ensure_list(data.get("reasons"))])[:4]

    if not reasons:
        reasons = ["Produit compréhensible en vidéo courte."]

    return {"score": score, "reasons": reasons}


def _generate_summary(context: Dict[str, Any], positioning: Dict[str, Any]) -> str:
    payload = {
        "task": "Génère une phrase courte de résumé marketing pour affichage liste / base de données.",
        "rules": [
            "Une seule phrase",
            "Français naturel",
            "Clair, court, spécifique au produit",
            "Pas de points d'exclamation multiples",
            "12 à 18 mots idéalement"
        ],
        "product_context": context,
        "positioning": positioning,
    }

    data = _call_block_json(
        schema=SUMMARY_JSON_SCHEMA,
        system_prompt="Tu écris un summary marketing court. Réponds uniquement en JSON.",
        user_payload=payload,
        temperature=0.1,
    )

    summary = _clean_str(data.get("summary"))
    if not summary:
        summary = _clean_str(positioning.get("main_promise"))
    if not summary:
        title = _clean_str(context.get("title")) or "Ce produit"
        summary = f"{title} apporte un bénéfice simple à comprendre et facile à montrer en vidéo."
    return summary


# =============================================================================
# PUBLIC GENERATION
# =============================================================================

def generate_analysis(product_payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    context = _build_product_context(product_payload, geo)

    if context.get("title"):
        context["title"] = _normalize_product_title(_ensure_french_title(context["title"], geo=geo), geo=geo)

    if not _clean_str(context.get("category")):
        context["category"] = _generate_category(context)
    elif context["category"] not in ALLOWED_CATEGORIES:
        context["category"] = "accessoires"

    if len(_ensure_list(context.get("tags"))) < 2:
        context["tags"] = _generate_tags(context)

    positioning = _generate_positioning(context)
    hooks = _generate_hooks(context, positioning)
    objections = _generate_objections(context, positioning)
    ugc_script = _generate_ugc_script(context, positioning, hooks)
    risks = _generate_risks(context, positioning)
    recommendations = _generate_recommendations(context, positioning)
    confidence = _generate_confidence(
        context=context,
        positioning=positioning,
        hooks=hooks,
        objections=objections,
        ugc_script=ugc_script,
        risks=risks,
        recommendations=recommendations,
    )

    analysis = {
        "positioning": positioning,
        "angles": {
            "hooks": hooks,
            "objections": objections,
            "ugc_script": ugc_script,
        },
        "risks": risks,
        "recommendations": recommendations,
        "confidence": confidence,
    }
    return _postprocess_analysis(analysis)


def generate_summary(product_payload: Dict[str, Any], geo: str = "FR") -> str:
    context = _build_product_context(product_payload, geo)

    if context.get("title"):
        context["title"] = _normalize_product_title(_ensure_french_title(context["title"], geo=geo), geo=geo)

    if not _clean_str(context.get("category")):
        context["category"] = _generate_category(context)
    elif context["category"] not in ALLOWED_CATEGORIES:
        context["category"] = "accessoires"

    if len(_ensure_list(context.get("tags"))) < 2:
        context["tags"] = _generate_tags(context)

    positioning = _generate_positioning(context)
    return _generate_summary(context, positioning)


def enrich_product_payload(product_payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    context = _build_product_context(product_payload, geo)

    if context.get("title"):
        context["title"] = _normalize_product_title(_ensure_french_title(context["title"], geo=geo), geo=geo)

    if not _clean_str(context.get("category")):
        context["category"] = _generate_category(context)
    elif context["category"] not in ALLOWED_CATEGORIES:
        context["category"] = "accessoires"

    if len(_ensure_list(context.get("tags"))) < 2:
        context["tags"] = _generate_tags(context)

    analysis = generate_analysis(
        {
            **product_payload,
            "title": context["title"],
            "category": context["category"],
            "tags": context["tags"],
        },
        geo=geo,
    )

    summary = _generate_summary(context, analysis.get("positioning", {}))
    title = _clean_str(context["title"]) or "ce produit"

    return {
        **product_payload,
        "title": title,
        "slug": _slugify(_clean_str(product_payload.get("slug")) or title),
        "category": context["category"],
        "tags": context["tags"],
        "summary": summary,
        "analysis": analysis,
    }


# =============================================================================
# OPTIONAL: PIPELINE HELPER
# =============================================================================

def analyze_from_caption(caption: str, geo: str = "FR") -> Dict[str, Any]:
    name = extract_product_name(caption, geo)
    if not name:
        return {"ok": False, "reason": "no_product_found"}

    sell = classify_sellability(name, geo)
    if not sell["sellable"]:
        return {"ok": False, "reason": "not_sellable", "sellability": sell, "product": name}

    payload = {
        "title": name,
        "source_caption": caption,
    }

    enriched = enrich_product_payload(payload, geo=geo)

    return {
        "ok": True,
        "product": name,
        "sellability": sell,
        "title": enriched["title"],
        "slug": enriched["slug"],
        "category": enriched["category"],
        "tags": enriched["tags"],
        "summary": enriched["summary"],
        "analysis": enriched["analysis"],
    }