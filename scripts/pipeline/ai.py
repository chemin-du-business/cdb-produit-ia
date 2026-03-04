from __future__ import annotations

import os
import json
from typing import Any, Dict, List
from openai import OpenAI

client = OpenAI(api_key=(os.environ.get("OPENAI_API_KEY") or "").strip())


def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"


def _safe_json_load(s: str) -> Dict[str, Any]:
    s = (s or "").strip()
    if not s:
        return {}
    # tentative directe
    try:
        return json.loads(s)
    except Exception:
        pass
    # extraction du premier bloc JSON
    try:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(s[start : end + 1])
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


def _default_analysis(title: str) -> Dict[str, Any]:
    # fallback "rempli" (pas vide) si IA KO
    return {
        "risks": [{"note": "Concurrence possible sur ce type de produit.", "type": "concurrence", "level": "medium"}],
        "angles": {
            "hooks": [
                f"Tout le monde parle de {title}… et tu vas comprendre pourquoi",
                f"Le truc simple qui rend {title} beaucoup plus efficace",
                f"Si tu as déjà galéré avec [problème], {title} peut te sauver",
            ],
            "objections": [
                {"objection": "Ça a l’air gadget", "response": "Justement : on montre la démo avant/après en 5 secondes."},
                {"objection": "Je ne sais pas si ça marche", "response": "On prouve l’effet avec une vidéo UGC + preuve sociale."},
            ],
            "ugc_script": {
                "script": (
                    f"J’avais un vrai problème avec [problème]… puis j’ai testé {title}. "
                    "Regarde la différence en 5 secondes. "
                    "Si tu veux le même résultat, lien en bio / en description."
                ),
                "duration_seconds": 20,
            },
        },
        "confidence": {"score": 6, "reasons": ["Signal TikTok observé", "Produit simple à comprendre en vidéo"]},
        "positioning": {
            "why_now": "Les formats UGC courts boostent les produits démontrables.",
            "main_promise": "Résultat visible rapidement avec un usage simple.",
            "problem_solved": "Résout un irritant du quotidien / améliore le confort ou l’efficacité.",
            "target_customer": "Public grand public (18-45) sensible aux contenus TikTok et aux produits pratiques.",
        },
        "recommendations": {
            "upsells": ["Pack de recharges / accessoires", "Version premium / bundle"],
            "channels": ["TikTok Ads", "UGC organique", "Shopify + retargeting"],
            "price_range": {"min": 19, "max": 49, "currency": "EUR"},
        },
    }


def _build_user_payload(payload: Dict[str, Any], geo: str) -> Dict[str, Any]:
    title = (payload.get("title") or "").strip()
    category = (payload.get("category") or "autre").strip()
    tags = payload.get("tags") or []
    signals = payload.get("signals") or {}
    tk = _ensure_dict(signals.get("tiktok_hashtag"))

    return {
        "product": {"title": title, "category": category, "tags": tags, "market": geo},
        "tiktok_signal": {
            "views": int(tk.get("views", 0) or 0),
            "likes": int(tk.get("likes", 0) or 0),
            "shares": int(tk.get("shares", 0) or 0),
            "comments": int(tk.get("comments", 0) or 0),
            "created_at": tk.get("created_at"),
            "video_url": tk.get("video_url"),
        },
        "output_required": {
            "risks": [{"note": "string", "type": "string", "level": "low|medium|high"}],
            "angles": {
                "hooks": ["string", "string", "string"],
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
        "constraints": [
            "Retourne UNIQUEMENT le JSON final, sans texte, sans markdown.",
            "Pas de '...', pas de champs vides.",
            "Hooks: 4 à 7 hooks courts, style TikTok FR.",
            "Objections: 3 à 6 objections/réponses concrètes.",
            "UGC script: 15 à 30 secondes, très 'parlé', avec démo.",
            "Confidence.score: 1..10.",
            "Price_range: min/max réalistes FR pour e-commerce (ex: 19-79).",
        ],
    }


def _normalize_analysis(data: Dict[str, Any], title: str) -> Dict[str, Any]:
    # force structure + remplit si vide
    risks = _ensure_list(data.get("risks"))
    angles = _ensure_dict(data.get("angles"))
    confidence = _ensure_dict(data.get("confidence"))
    positioning = _ensure_dict(data.get("positioning"))
    recommendations = _ensure_dict(data.get("recommendations"))

    # risks
    out_risks = []
    for r in risks:
        rr = _ensure_dict(r)
        out_risks.append(
            {
                "note": _clean_str(rr.get("note")),
                "type": _clean_str(rr.get("type")),
                "level": _clean_str(rr.get("level")) or "medium",
            }
        )
    if not out_risks or not out_risks[0]["note"]:
        out_risks = [{"note": "Concurrence possible sur ce type de produit.", "type": "concurrence", "level": "medium"}]

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

    # auto-fill si vide
    if len(hooks) < 3:
        hooks = [
            f"Le produit {title} dont TikTok parle partout",
            f"Tu vas vouloir {title} après avoir vu ça",
            f"Avant/Après : {title} en 10 secondes",
            f"Le hack simple que {title} rend possible",
        ]
    if len(objections) < 2:
        objections = [
            {"objection": "Ça a l’air gadget", "response": "On montre le résultat en démo (avant/après) en 5 secondes."},
            {"objection": "Trop cher", "response": "Moins cher qu’une alternative pro + utile tous les jours."},
            {"objection": "Je ne suis pas sûr que ça marche", "response": "UGC + preuve sociale + garantie satisfait ou remboursé."},
        ]
    if not ugc_script["script"]:
        ugc_script["script"] = (
            f"J’avais un vrai problème avec [problème]… puis j’ai testé {title}. "
            "Regarde la démo : (avant) … (après) … "
            "Si tu veux le même résultat, je te mets le lien."
        )
        ugc_script["duration_seconds"] = 20
    ugc_script["duration_seconds"] = max(15, min(30, int(ugc_script["duration_seconds"] or 20)))

    # confidence
    conf_score = int(confidence.get("score") or 6)
    conf_score = max(1, min(10, conf_score))
    conf_reasons = [_clean_str(x) for x in _ensure_list(confidence.get("reasons")) if _clean_str(x)]
    if not conf_reasons:
        conf_reasons = ["Signal TikTok observé", "Produit démontrable en vidéo", "Problème simple et universel"]

    # positioning
    pos = {
        "why_now": _clean_str(positioning.get("why_now")) or "Format UGC + démonstration = fort potentiel de conversion.",
        "main_promise": _clean_str(positioning.get("main_promise")) or "Résultat visible rapidement avec un usage simple.",
        "problem_solved": _clean_str(positioning.get("problem_solved")) or "Résout un irritant du quotidien / améliore le confort.",
        "target_customer": _clean_str(positioning.get("target_customer")) or "Grand public 18-45, acheteurs impulsifs e-commerce.",
    }

    # recommendations
    price = _ensure_dict(recommendations.get("price_range"))
    pr_min = int(price.get("min") or 19)
    pr_max = int(price.get("max") or 49)
    if pr_max < pr_min:
        pr_max = pr_min + 10
    pr_min = max(9, pr_min)
    pr_max = min(199, pr_max)

    upsells = [_clean_str(x) for x in _ensure_list(recommendations.get("upsells")) if _clean_str(x)]
    channels = [_clean_str(x) for x in _ensure_list(recommendations.get("channels")) if _clean_str(x)]
    if not channels:
        channels = ["TikTok Ads", "UGC organique", "Retargeting"]

    return {
        "risks": out_risks[:6],
        "angles": {"hooks": hooks[:7], "objections": objections[:6], "ugc_script": ugc_script},
        "confidence": {"score": conf_score, "reasons": conf_reasons[:6]},
        "positioning": pos,
        "recommendations": {
            "upsells": upsells[:6] or ["Bundle / pack", "Accessoires complémentaires"],
            "channels": channels[:6],
            "price_range": {"min": pr_min, "max": pr_max, "currency": "EUR"},
        },
    }


def generate_analysis(payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    title = (payload.get("title") or "").strip()
    if not title:
        return _default_analysis("ce produit")

    user_payload = _build_user_payload(payload, geo)

    system = (
        "Tu es un expert e-commerce FR. "
        "Tu dois produire un JSON COMPLET au format demandé, sans champs vides. "
        "Retourne UNIQUEMENT le JSON final, sans markdown."
    )

    # 2 tentatives (retry) pour éviter fallback
    last_txt = ""
    for _ in range(2):
        resp = client.chat.completions.create(
            model=_model(),
            temperature=0.5,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )
        last_txt = (resp.choices[0].message.content or "").strip()
        data = _safe_json_load(last_txt)
        if data:
            return _normalize_analysis(data, title)

    # si ça échoue, fallback rempli (pas vide)
    return _default_analysis(title)