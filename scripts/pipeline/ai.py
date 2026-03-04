from __future__ import annotations

import os
import json
from typing import Any, Dict, List
from openai import OpenAI

client = OpenAI(api_key=(os.environ.get("OPENAI_API_KEY") or "").strip())


def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"


def _safe_json_load(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        # parfois le modèle renvoie du texte avant/après : on tente d'extraire le premier bloc JSON
        try:
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(s[start : end + 1])
        except Exception:
            pass
    return {}


def _ensure_list(x: Any) -> List[Any]:
    if isinstance(x, list):
        return x
    return []


def _ensure_dict(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    return {}


def extract_product_name(caption: str, geo: str = "FR") -> str:
    caption = (caption or "").strip()
    if not caption:
        return ""

    resp = client.chat.completions.create(
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

    resp = client.chat.completions.create(
        model=_model(),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Réponds uniquement par OUI ou NON. "
                    "OUI seulement si c'est un produit e-commerce concret vendable (objet, accessoire, équipement). "
                    "NON si c'est une personne, politique, match, événement, film, musique, actualité, score, ou terme abstrait."
                ),
            },
            {"role": "user", "content": f"Terme: {term} (marché {geo})"},
        ],
    )

    txt = (resp.choices[0].message.content or "").strip().upper()
    return txt.startswith("OUI")


def generate_analysis(payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    """
    Retourne EXACTEMENT le JSON final demandé (sans output_schema, sans '...').
    Utilise les signaux TikTok (views/likes/shares + date) pour justifier.
    """
    title = (payload.get("title") or "").strip()
    category = (payload.get("category") or "autre").strip()
    tags = payload.get("tags") or []
    signals = payload.get("signals") or {}
    sources = payload.get("sources") or []

    # On extrait les stats TikTok utiles (si présentes)
    tk = _ensure_dict(signals.get("tiktok_hashtag"))
    views = int(tk.get("views", 0) or 0)
    likes = int(tk.get("likes", 0) or 0)
    shares = int(tk.get("shares", 0) or 0)
    comments = int(tk.get("comments", 0) or 0)
    created_at = tk.get("created_at")
    video_url = tk.get("video_url")

    # Prompt clair : PAS de schéma placeholder, juste la sortie finale
    system = (
        "Tu es un expert e-commerce français (dropshipping / ads / UGC). "
        "Retourne UNIQUEMENT un JSON valide (pas de markdown, pas de texte). "
        "Le JSON doit être EXACTEMENT au format demandé, avec des valeurs remplies (pas de '...', pas de champs 'output_schema'). "
        "Sois concret, orienté conversion, et adapté au marché FR."
    )

    user = {
        "product": {
            "title": title,
            "category": category,
            "tags": tags,
            "market": geo,
        },
        "signals": {
            "tiktok": {
                "views": views,
                "likes": likes,
                "shares": shares,
                "comments": comments,
                "created_at": created_at,
                "video_url": video_url,
            },
            "sources": sources,
        },
        "required_output_format": {
            "risks": [{"note": "string", "type": "string", "level": "low|medium|high"}],
            "angles": {
                "hooks": ["string", "string"],
                "objections": [{"objection": "string", "response": "string"}],
                "ugc_script": {"script": "string", "duration_seconds": 20},
            },
            "confidence": {"score": 1, "reasons": ["string"]},
            "positioning": {
                "why_now": "string",
                "main_promise": "string",
                "problem_solved": "string",
                "target_customer": "string",
            },
            "recommendations": {
                "upsells": ["string"],
                "channels": ["string"],
                "price_range": {"min": 0, "max": 0, "currency": "EUR"},
            },
        },
        "rules": [
            "Pas de champs en plus.",
            "Pas de placeholder '...'.",
            "Remplis tout avec du contenu réaliste.",
            "Price_range min/max réalistes pour la France.",
            "confidence.score doit être 1..10.",
            "ugc_script.duration_seconds entre 15 et 30.",
        ],
    }

    resp = client.chat.completions.create(
        model=_model(),
        temperature=0.35,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
    )

    txt = (resp.choices[0].message.content or "").strip()
    data = _safe_json_load(txt)

    # ---- Validation + normalisation (garantit un JSON exploitable) ----
    if not data:
        return {
            "risks": [{"note": "Analyse non disponible (JSON invalide).", "type": "ai", "level": "medium"}],
            "angles": {
                "hooks": [],
                "objections": [],
                "ugc_script": {"script": "", "duration_seconds": 20},
            },
            "confidence": {"score": 5, "reasons": ["Signal TikTok détecté"]},
            "positioning": {
                "why_now": "",
                "main_promise": "",
                "problem_solved": "",
                "target_customer": "",
            },
            "recommendations": {
                "upsells": [],
                "channels": ["TikTok"],
                "price_range": {"min": 19, "max": 49, "currency": "EUR"},
            },
        }

    # Garantit les clés attendues (et types)
    risks = _ensure_list(data.get("risks"))
    angles = _ensure_dict(data.get("angles"))
    confidence = _ensure_dict(data.get("confidence"))
    positioning = _ensure_dict(data.get("positioning"))
    recommendations = _ensure_dict(data.get("recommendations"))

    # Nettoyage basique pour éviter les "..."
    def _clean_str(s: Any) -> str:
        s = (str(s) if s is not None else "").strip()
        if s == "..." or s.lower() == "…":
            return ""
        return s

    # risks
    cleaned_risks = []
    for r in risks:
        rr = _ensure_dict(r)
        cleaned_risks.append(
            {
                "note": _clean_str(rr.get("note")),
                "type": _clean_str(rr.get("type")),
                "level": _clean_str(rr.get("level")) or "medium",
            }
        )

    # angles
    hooks = [_clean_str(x) for x in _ensure_list(angles.get("hooks")) if _clean_str(x)]
    objections = []
    for o in _ensure_list(angles.get("objections")):
        oo = _ensure_dict(o)
        objections.append({"objection": _clean_str(oo.get("objection")), "response": _clean_str(oo.get("response"))})
    ugc = _ensure_dict(angles.get("ugc_script"))
    ugc_script = {
        "script": _clean_str(ugc.get("script")),
        "duration_seconds": int(ugc.get("duration_seconds") or 20),
    }

    # confidence
    conf_score = int(confidence.get("score") or 5)
    conf_score = max(1, min(10, conf_score))
    conf_reasons = [_clean_str(x) for x in _ensure_list(confidence.get("reasons")) if _clean_str(x)]

    # positioning
    pos = {
        "why_now": _clean_str(positioning.get("why_now")),
        "main_promise": _clean_str(positioning.get("main_promise")),
        "problem_solved": _clean_str(positioning.get("problem_solved")),
        "target_customer": _clean_str(positioning.get("target_customer")),
    }

    # recommendations
    price = _ensure_dict(recommendations.get("price_range"))
    pr_min = int(price.get("min") or 19)
    pr_max = int(price.get("max") or 49)
    if pr_max < pr_min:
        pr_max = pr_min + 10

    rec = {
        "upsells": [_clean_str(x) for x in _ensure_list(recommendations.get("upsells")) if _clean_str(x)],
        "channels": [_clean_str(x) for x in _ensure_list(recommendations.get("channels")) if _clean_str(x)] or ["TikTok"],
        "price_range": {"min": pr_min, "max": pr_max, "currency": "EUR"},
    }

    return {
        "risks": cleaned_risks if cleaned_risks else [{"note": "Risque de concurrence", "type": "concurrence", "level": "medium"}],
        "angles": {
            "hooks": hooks[:6],
            "objections": objections[:6],
            "ugc_script": ugc_script,
        },
        "confidence": {"score": conf_score, "reasons": conf_reasons[:6] or ["Signal TikTok observé"]},
        "positioning": pos,
        "recommendations": rec,
    }