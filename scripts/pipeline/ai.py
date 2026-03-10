from __future__ import annotations

import os
import json
import time
import random
import re
from typing import Any, Dict, List, Optional

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
# RESPONSE_FORMAT SUPPORT (best effort)
# =============================================================================

def _chat_json_best_effort(
    *,
    model: str,
    temperature: float,
    messages: List[Dict[str, str]],
) -> str:
    try:
        resp = _chat_with_retry(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=messages,
        )
        return (resp.choices[0].message.content or "").strip()
    except TypeError:
        pass
    except Exception:
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

    return txt[:80]


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
            "Sois strict. Si doute, sellable=false.",
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
    return bool(classify_sellability(term, geo).get("sellable", False))


# =============================================================================
# ANALYSIS SCHEMA
# =============================================================================

ANALYSIS_SCHEMA: Dict[str, Any] = {
    "positioning": {
        "main_promise": "",
        "target_customer": "",
        "problem_solved": "",
        "why_now": "",
    },
    "angles": {
        "hooks": ["", "", ""],
        "objections": [{"objection": "", "response": ""}],
        "ugc_script": {"script": "", "duration_seconds": 20},
    },
    "risks": [{"type": "", "level": "low", "note": ""}],
    "recommendations": {
        "price_range": {"min": 0, "max": 0, "currency": "EUR"},
        "channels": ["TikTok Ads"],
        "upsells": [""],
    },
    "confidence": {"score": 0, "reasons": [""]},
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

    hooks = _uniq_keep_order([_clean_str(x) for x in _ensure_list(_ensure_dict(out["angles"]).get("hooks"))])
    out["angles"]["hooks"] = hooks[:3]

    obj = _ensure_list(_ensure_dict(out["angles"]).get("objections"))
    cleaned_obj: List[Dict[str, str]] = []
    for it in obj[:3]:
        d = _ensure_dict(it)
        objection = _clean_str(d.get("objection"))
        response = _clean_str(d.get("response"))
        if objection and response:
            cleaned_obj.append({"objection": objection, "response": response})
    out["angles"]["objections"] = cleaned_obj

    ugc = _ensure_dict(_ensure_dict(out["angles"]).get("ugc_script"))
    dur = _coerce_int(ugc.get("duration_seconds"), 20)
    out["angles"]["ugc_script"] = {
        "script": _clean_str(ugc.get("script")),
        "duration_seconds": int(_clamp(dur, 5, 60)),
    }

    risks = _ensure_list(out.get("risks"))
    norm: List[Dict[str, str]] = []
    for r in risks[:5]:
        d = _ensure_dict(r)
        lvl = _clean_str(d.get("level")).lower()
        if lvl not in ("low", "medium", "high"):
            lvl = "low"
        risk_type = _clean_str(d.get("type"))
        note = _clean_str(d.get("note"))
        if risk_type or note:
            norm.append({
                "type": risk_type,
                "level": lvl,
                "note": note,
            })
    out["risks"] = norm

    conf = _ensure_dict(out.get("confidence"))
    cs = _coerce_int(conf.get("score"), 0)
    reasons = _uniq_keep_order([_clean_str(x) for x in _ensure_list(conf.get("reasons"))])
    out["confidence"] = {
        "score": int(_clamp(cs, 0, 10)),
        "reasons": reasons,
    }

    pr = _ensure_dict(_ensure_dict(out.get("recommendations")).get("price_range"))
    mn = _coerce_int(pr.get("min"), 0)
    mx = _coerce_int(pr.get("max"), 0)
    mn = int(_clamp(mn, 0, 9999))
    mx = int(_clamp(mx, 0, 9999))
    if mn and mx and mn > mx:
        mn, mx = mx, mn

    rec = _ensure_dict(out.get("recommendations"))
    out["recommendations"] = {
        "price_range": {
            "min": mn,
            "max": mx,
            "currency": _clean_str(pr.get("currency")) or "EUR",
        },
        "channels": _uniq_keep_order([_clean_str(x) for x in _ensure_list(rec.get("channels"))]),
        "upsells": _uniq_keep_order([_clean_str(x) for x in _ensure_list(rec.get("upsells"))]),
    }

    pos = _ensure_dict(out.get("positioning"))
    out["positioning"] = {
        "main_promise": _clean_str(pos.get("main_promise")),
        "target_customer": _clean_str(pos.get("target_customer")),
        "problem_solved": _clean_str(pos.get("problem_solved")),
        "why_now": _clean_str(pos.get("why_now")),
    }

    return out


# =============================================================================
# VALIDATION
# =============================================================================

def _is_placeholder_text(s: Any) -> bool:
    t = _clean_str(s).lower()
    if not t:
        return True

    bad = {
        "...",
        "…",
        "[problème]",
        "[probleme]",
        "[douleur]",
        "[pain point]",
        "n/a",
        "na",
        "none",
        "null",
        "à compléter",
        "a completer",
    }
    if t in bad:
        return True
    if "[" in t or "]" in t:
        return True
    return False


def _analysis_missing_fields(a: Dict[str, Any]) -> List[str]:
    missing: List[str] = []

    pos = _ensure_dict(a.get("positioning"))
    for k in ("main_promise", "target_customer", "problem_solved", "why_now"):
        if _is_placeholder_text(pos.get(k)):
            missing.append(f"positioning.{k}")

    angles = _ensure_dict(a.get("angles"))

    hooks = _ensure_list(angles.get("hooks"))
    clean_hooks = [h for h in hooks if not _is_placeholder_text(h)]
    if len(clean_hooks) < 3:
        missing.append("angles.hooks")

    objections = _ensure_list(angles.get("objections"))
    valid_objections = 0
    for o in objections:
        d = _ensure_dict(o)
        if not _is_placeholder_text(d.get("objection")) and not _is_placeholder_text(d.get("response")):
            valid_objections += 1
    if valid_objections < 2:
        missing.append("angles.objections")

    ugc = _ensure_dict(angles.get("ugc_script"))
    if _is_placeholder_text(ugc.get("script")):
        missing.append("angles.ugc_script.script")

    risks = _ensure_list(a.get("risks"))
    valid_risks = 0
    for r in risks:
        d = _ensure_dict(r)
        if (
            not _is_placeholder_text(d.get("type"))
            and not _is_placeholder_text(d.get("note"))
            and _clean_str(d.get("level")).lower() in ("low", "medium", "high")
        ):
            valid_risks += 1
    if valid_risks < 1:
        missing.append("risks")

    rec = _ensure_dict(a.get("recommendations"))
    channels = [x for x in _ensure_list(rec.get("channels")) if not _is_placeholder_text(x)]
    if len(channels) < 2:
        missing.append("recommendations.channels")

    upsells = [x for x in _ensure_list(rec.get("upsells")) if not _is_placeholder_text(x)]
    if len(upsells) < 1:
        missing.append("recommendations.upsells")

    conf = _ensure_dict(a.get("confidence"))
    if _coerce_int(conf.get("score"), 0) <= 0:
        missing.append("confidence.score")
    reasons = [x for x in _ensure_list(conf.get("reasons")) if not _is_placeholder_text(x)]
    if len(reasons) < 1:
        missing.append("confidence.reasons")

    return missing


def _analysis_is_valid(a: Dict[str, Any]) -> bool:
    return len(_analysis_missing_fields(a)) == 0


# =============================================================================
# JSON REPAIR
# =============================================================================

def _repair_to_schema(raw_text: str, product_payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    raw_data = _safe_json_load(raw_text)
    if not raw_data:
        raw_data = {}

    missing = _analysis_missing_fields(raw_data)

    prompt = {
        "task": "Complète uniquement les champs manquants ou invalides pour produire un JSON final valide.",
        "market": geo,
        "product": product_payload,
        "current_json": raw_data,
        "missing_fields": missing,
        "rules": [
            "Retourne uniquement un JSON valide.",
            "Garde exactement le même schéma.",
            "Interdiction de laisser des chaînes vides, ..., … ou placeholders entre crochets.",
            "Les hooks doivent être concrets, spécifiques et publiables.",
            "Les objections doivent contenir objection ET response.",
            "Le script UGC doit être complet et naturel.",
            "Sois spécifique au produit fourni.",
        ],
        "schema": ANALYSIS_SCHEMA,
    }

    txt = _chat_json_best_effort(
        model=_model(),
        temperature=0.2,
        messages=[
            {"role": "system", "content": "Réponds uniquement en JSON valide, complet, sans placeholders."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )

    return _safe_json_load(txt)


# =============================================================================
# GENERATE ANALYSIS
# =============================================================================

def generate_analysis(product_payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    title = _clean_str(product_payload.get("title") or product_payload.get("name") or "")
    if not title:
        title = "ce produit"

    prompt = {
        "market": geo,
        "schema": ANALYSIS_SCHEMA,
        "product": product_payload,
        "instructions": [
            "Tu es un expert e-commerce et copywriting direct response.",
            "Retourne uniquement un JSON valide.",
            "Respecte exactement le schéma fourni, sans clé en plus.",
            "Aucun champ important ne doit être vide.",
            "Interdiction d'utiliser : ..., …, [problème], [douleur], placeholders ou texte générique non exploitable.",
            "Les hooks doivent être courts, concrets, spécifiques au produit, publiables tels quels.",
            "Donne exactement 3 hooks.",
            "Donne 2 à 3 objections maximum, chaque objection doit avoir une objection ET une réponse complètes.",
            "Le script UGC doit être complet, naturel, crédible et spécifique au produit.",
            "Le positioning doit être concret et exploitable pour une fiche produit ou une pub.",
            "Les risques doivent être réalistes et spécifiques.",
            "Les channels et upsells doivent être cohérents avec le produit.",
            "Ne laisse aucun champ stratégique vide.",
        ],
        "title": title,
    }

    txt = _chat_json_best_effort(
        model=_model(),
        temperature=0.4,
        messages=[
            {"role": "system", "content": "Réponds uniquement en JSON valide, complet, sans placeholders."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )

    data = _safe_json_load(txt)

    if data and _analysis_is_valid(data):
        return _postprocess_analysis(data)

    repaired = _repair_to_schema(txt, product_payload, geo)
    if repaired and _analysis_is_valid(repaired):
        return _postprocess_analysis(repaired)

    txt2 = _chat_json_best_effort(
        model=_model(),
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Réponds uniquement en JSON valide. "
                    "Aucun champ vide. Aucun placeholder. "
                    "Si un champ est manquant, complète-le de manière spécifique au produit."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "product": product_payload,
                        "market": geo,
                        "schema": ANALYSIS_SCHEMA,
                        "missing_requirements": _analysis_missing_fields(data or {}),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    )

    data2 = _safe_json_load(txt2)
    if data2 and _analysis_is_valid(data2):
        return _postprocess_analysis(data2)

    best = data2 or repaired or data or {}
    return _postprocess_analysis(best)


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

    payload = {"title": name, "source_caption": caption}
    analysis = generate_analysis(payload, geo)

    return {"ok": True, "product": name, "sellability": sell, "analysis": analysis}