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


def _coerce_int(x: Any, default: int) -> int:
    try:
        if x is None:
            return default
        if isinstance(x, bool):
            return default
        if isinstance(x, (int, float)):
            return int(x)
        s = str(x).strip().replace(",", ".")
        return int(float(s))
    except Exception:
        return default


def _coerce_float(x: Any, default: float) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, bool):
            return default
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip().replace("€", "").replace(",", ".")
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
    # (garde le format existant pour ne pas casser la page)
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
    """
    IMPORTANT: on enrichit l'entrée (sans rien casser si pas fourni),
    et on remplace output_required (template "string") par output_format (anti-générique).
    """
    title = (payload.get("title") or "").strip()
    category = (payload.get("category") or "autre").strip()
    tags = payload.get("tags") or []
    signals = payload.get("signals") or {}
    tk = _ensure_dict(signals.get("tiktok_hashtag"))

    # champs optionnels (si l'appelant les fournit, l'IA devient nettement moins générique)
    attributes = _ensure_dict(payload.get("attributes"))
    use_case = _clean_str(payload.get("use_case"))
    differentiators = _ensure_list(payload.get("differentiators"))
    competitors = _ensure_list(payload.get("competitors"))
    commercial = _ensure_dict(payload.get("commercial"))
    shipping = _ensure_dict(payload.get("shipping"))
    compliance = _ensure_dict(payload.get("compliance"))

    return {
        "product": {
            "title": title,
            "category": category,
            "tags": tags,
            "market": geo,
            "use_case": use_case,
            "attributes": attributes,
            "differentiators": differentiators,
        },
        "market_context": {
            "known_competitors": competitors,
            "primary_platforms": _ensure_list(payload.get("primary_platforms")) or ["TikTok", "Shopify"],
        },
        "commercial": {
            "target_price": commercial.get("target_price"),
            "cogs_estimate": commercial.get("cogs_estimate"),
            "shipping_estimate": commercial.get("shipping_estimate"),
            "shipping": shipping,
            "target_margin": commercial.get("target_margin"),
            "vat_included": commercial.get("vat_included", True),
        },
        "compliance": {
            "touches_skin": bool(compliance.get("touches_skin", payload.get("touches_skin", False))),
            "for_children": bool(compliance.get("for_children", payload.get("for_children", False))),
            "medical_claims": bool(compliance.get("medical_claims", payload.get("medical_claims", False))),
        },
        "tiktok_signal": {
            "views": int(tk.get("views", 0) or 0),
            "likes": int(tk.get("likes", 0) or 0),
            "shares": int(tk.get("shares", 0) or 0),
            "comments": int(tk.get("comments", 0) or 0),
            "created_at": tk.get("created_at"),
            "video_url": tk.get("video_url"),
        },
        "output_format": {
            "risks": "array<{note:string,type:string,level:'low'|'medium'|'high'}> (3-6 risques spécifiques)",
            "angles": {
                "hooks": "array<string> (4-7 hooks TikTok FR, spécifiques au produit, sans phrases génériques)",
                "objections": "array<{objection:string,response:string}> (3-6, concrètes et liées au produit)",
                "ugc_script": "object<{script:string,duration_seconds:int}> (15-30s, parlé, avec démo spécifique)",
            },
            "confidence": "object<{score:int(1..10),reasons:array<string>(3-6)}> (raisons spécifiques)",
            "positioning": "object<{why_now,main_promise,problem_solved,target_customer}> (sans blabla générique)",
            "recommendations": {
                "upsells": "array<string> (2-6, cohérents avec le produit)",
                "channels": "array<string> (2-6, cohérents marché FR)",
                "price_range": "object<{min:number,max:number,currency:'EUR'}> (min/max réalistes et justifiés implicitement)",
            },
        },
        "constraints": [
            "Retourne UNIQUEMENT le JSON final, sans texte, sans markdown.",
            "Aucun champ vide. Aucun '...'. Aucun placeholder du type [problème].",
            "Interdit d'utiliser des formulations vagues type 'produit pratique', 'résultat visible rapidement', 'concurrence possible' sans préciser POURQUOI pour CE produit.",
            "Chaque risque doit être différent ET lié à un détail du produit (matière/usage/catégorie/logistique/conformité/retours/SAV/saturation).",
            "Hooks: 4 à 7 hooks courts (<= 12 mots si possible), style TikTok FR, incluant un bénéfice/usage/démo spécifique.",
            "Objections: 3 à 6 objections/réponses concrètes, adaptées au produit (prix, efficacité, sécurité, taille, entretien, SAV, compatibilité...).",
            "UGC script: 15 à 30 secondes, très parlé, avec une démo avant/après OU un test concret lié au produit.",
            "Confidence.score: 1..10. Reasons: 3..6, spécifiques aux signaux et au produit.",
            "Price_range: min/max en EUR réalistes pour e-commerce FR selon catégorie/complexité/attributs/coûts si fournis. Pas de valeur par défaut.",
        ],
    }


def _needs_repair(data: Dict[str, Any]) -> bool:
    """
    Détecte les sorties trop incomplètes/génériques -> on déclenche un 2e call "repair".
    Simple et safe (n'affecte pas si la sortie est bonne).
    """
    if not isinstance(data, dict) or not data:
        return True

    angles = _ensure_dict(data.get("angles"))
    hooks = _ensure_list(angles.get("hooks"))
    objections = _ensure_list(angles.get("objections"))
    ugc = _ensure_dict(angles.get("ugc_script"))

    risks = _ensure_list(data.get("risks"))
    positioning = _ensure_dict(data.get("positioning"))
    recommendations = _ensure_dict(data.get("recommendations"))
    price = _ensure_dict(recommendations.get("price_range"))
    confidence = _ensure_dict(data.get("confidence"))

    # minimums
    if len(hooks) < 4:
        return True
    if len(objections) < 3:
        return True
    if len(risks) < 3:
        return True

    if not _clean_str(ugc.get("script")):
        return True

    # positioning complet
    for k in ("why_now", "main_promise", "problem_solved", "target_customer"):
        if not _clean_str(positioning.get(k)):
            return True

    # confidence
    score = confidence.get("score")
    if score is None:
        return True
    if len(_ensure_list(confidence.get("reasons"))) < 3:
        return True

    # price_range présent
    if price.get("min") is None or price.get("max") is None:
        return True

    return False


def _repair_analysis(original: Dict[str, Any], user_payload: Dict[str, Any], title: str) -> Dict[str, Any]:
    """
    2e passe: on demande au modèle de corriger/compléter UNIQUEMENT ce qui est faible ou générique,
    en restant dans le même format JSON (pour ne pas casser la page).
    """
    system = (
        "Tu es un expert e-commerce FR et copywriter TikTok. "
        "Tu vas RECEVOIR un JSON 'draft' et tu dois l'AMÉLIORER : "
        "le rendre spécifique au produit, non générique, sans placeholders, et complet. "
        "IMPORTANT: conserve EXACTEMENT la structure et les clés attendues (risks/angles/confidence/positioning/recommendations). "
        "Retourne UNIQUEMENT le JSON final, sans markdown."
    )

    repair_instructions = {
        "product_context": user_payload.get("product", {}),
        "tiktok_signal": user_payload.get("tiktok_signal", {}),
        "commercial": user_payload.get("commercial", {}),
        "market_context": user_payload.get("market_context", {}),
        "compliance": user_payload.get("compliance", {}),
        "draft_to_improve": original,
        "repair_rules": [
            "Remplace tout élément générique par des versions spécifiques au produit (bénéfice, usage, démo, contrainte).",
            "Risks: 3-6 risques différents, chacun avec une cause concrète et une conséquence business.",
            "Hooks: 4-7 hooks courts, pas de 'Tout le monde parle de...' sans angle concret.",
            "Objections: 3-6, orientées produit et marché FR.",
            "UGC script: 15-30s, parlé, avec une démo concrète liée au produit (test, avant/après, 'preuve').",
            "Price_range: propose min/max réalistes en EUR (peuvent être décimaux), adaptés à la catégorie + complexité + coûts si fournis.",
            "Confidence: score 1..10 + 3-6 raisons spécifiques (pas 'problème universel').",
            "Interdit: placeholders [x], '...', et phrases vides.",
        ],
        "title_hint": title,
    }

    resp = client.chat.completions.create(
        model=_model(),
        temperature=0.7,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(repair_instructions, ensure_ascii=False)},
        ],
    )
    txt = (resp.choices[0].message.content or "").strip()
    return _safe_json_load(txt)


def _normalize_analysis(data: Dict[str, Any], title: str) -> Dict[str, Any]:
    """
    IMPORTANT: on ne réinjecte plus de templates "génériques" sauf si l'IA est KO.
    Ici on valide + nettoie + borne, mais on évite d'écraser avec des valeurs par défaut.
    """
    # force structure
    risks = _ensure_list(data.get("risks"))
    angles = _ensure_dict(data.get("angles"))
    confidence = _ensure_dict(data.get("confidence"))
    positioning = _ensure_dict(data.get("positioning"))
    recommendations = _ensure_dict(data.get("recommendations"))

    # risks (on garde ce que l'IA donne, on nettoie)
    out_risks = []
    for r in risks:
        rr = _ensure_dict(r)
        note = _clean_str(rr.get("note"))
        typ = _clean_str(rr.get("type"))
        lvl = _clean_str(rr.get("level")) or "medium"
        if note:
            out_risks.append({"note": note, "type": typ or "autre", "level": lvl})
    out_risks = out_risks[:6]

    # angles
    hooks = _uniq_keep_order([_clean_str(x) for x in _ensure_list(angles.get("hooks"))])[:7]
    objections = []
    for o in _ensure_list(angles.get("objections")):
        oo = _ensure_dict(o)
        ob = _clean_str(oo.get("objection"))
        rp = _clean_str(oo.get("response"))
        if ob and rp:
            objections.append({"objection": ob, "response": rp})
    objections = objections[:6]

    ugc = _ensure_dict(angles.get("ugc_script"))
    ugc_script = {
        "script": _clean_str(ugc.get("script")),
        "duration_seconds": _coerce_int(ugc.get("duration_seconds"), 20),
    }
    ugc_script["duration_seconds"] = max(15, min(30, ugc_script["duration_seconds"]))

    # confidence
    conf_score = _coerce_int(confidence.get("score"), 6)
    conf_score = max(1, min(10, conf_score))
    conf_reasons = _uniq_keep_order([_clean_str(x) for x in _ensure_list(confidence.get("reasons"))])[:6]

    # positioning
    pos = {
        "why_now": _clean_str(positioning.get("why_now")),
        "main_promise": _clean_str(positioning.get("main_promise")),
        "problem_solved": _clean_str(positioning.get("problem_solved")),
        "target_customer": _clean_str(positioning.get("target_customer")),
    }

    # recommendations
    upsells = _uniq_keep_order([_clean_str(x) for x in _ensure_list(recommendations.get("upsells"))])[:6]
    channels = _uniq_keep_order([_clean_str(x) for x in _ensure_list(recommendations.get("channels"))])[:6]

    price = _ensure_dict(recommendations.get("price_range"))
    pr_min = _coerce_float(price.get("min"), 0.0)
    pr_max = _coerce_float(price.get("max"), 0.0)

    # bornes raisonnables FR ecom (sans imposer un template)
    # si l'IA a mis des valeurs hors-sol, on clamp; si elle n'a rien mis, on laisse 0..0
    if pr_min > 0:
        pr_min = _clamp(pr_min, 5.0, 499.0)
    if pr_max > 0:
        pr_max = _clamp(pr_max, 5.0, 499.0)
    if pr_min > 0 and pr_max > 0 and pr_max < pr_min:
        pr_max = pr_min + 10.0

    return {
        "risks": out_risks,
        "angles": {"hooks": hooks, "objections": objections, "ugc_script": ugc_script},
        "confidence": {"score": conf_score, "reasons": conf_reasons},
        "positioning": pos,
        "recommendations": {
            "upsells": upsells,
            "channels": channels,
            "price_range": {"min": pr_min, "max": pr_max, "currency": "EUR"},
        },
    }


def generate_analysis(payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    title = (payload.get("title") or "").strip()
    if not title:
        return _default_analysis("ce produit")

    user_payload = _build_user_payload(payload, geo)

    system = (
        "Tu es un expert e-commerce FR et copywriter TikTok. "
        "Tu dois produire un JSON COMPLET au format demandé, sans champs vides, et NON GÉNÉRIQUE. "
        "Tu dois adapter hooks/objections/risques/positioning/reco/price_range/ugc au produit (titre, catégorie, attributs, use_case, différenciateurs, signal TikTok, coûts si fournis). "
        "Retourne UNIQUEMENT le JSON final, sans markdown."
    )

    # 1) génération
    resp = client.chat.completions.create(
        model=_model(),
        temperature=0.8,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    )
    txt = (resp.choices[0].message.content or "").strip()
    data = _safe_json_load(txt)

    # 2) repair si incomplet / trop faible
    if _needs_repair(data):
        repaired = _repair_analysis(data or {}, user_payload, title)
        if repaired:
            data = repaired

    # 3) normalize (nettoyage/validation) ou fallback si KO total
    if data:
        normalized = _normalize_analysis(data, title)

        # sécurité: si encore trop vide (IA KO), fallback
        if (
            not normalized.get("angles", {}).get("hooks")
            or not normalized.get("angles", {}).get("ugc_script", {}).get("script")
            or not normalized.get("positioning", {}).get("main_promise")
        ):
            return _default_analysis(title)

        return normalized

    return _default_analysis(title)