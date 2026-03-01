from __future__ import annotations
import os, json, re
from typing import Any, Dict
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"

BLOCK_PATTERNS = [
    r"\brésultat\b", r"\bscore\b", r"\bmatch\b", r"\bligue\b", r"\bbut\b",
    r"\bélection\b", r"\bprésident\b", r"\bministre\b", r"\bguerre\b", r"\battaque\b",
    r"\bmétéo\b", r"\btrafic\b", r"\bgrève\b",
    r"\baccident\b", r"\bmort\b", r"\bdécès\b",
    r"\bfilm\b", r"\bsérie\b", r"\bacteur\b", r"\bactrice\b",
    r"\bconcert\b", r"\bfestival\b",
]
BRAND_BLOCKLIST = ["iphone","samsung","ps5","playstation","xbox","netflix","disney","tesla","apple","meta"]
_block_re = re.compile("|".join(BLOCK_PATTERNS), re.IGNORECASE)

def quick_reject(term: str) -> bool:
    t = (term or "").strip().lower()
    if not t:
        return True
    if _block_re.search(t):
        return True
    if any(b in t for b in BRAND_BLOCKLIST):
        return True
    if len(t) < 3:
        return True
    return False

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
        "output_json": {"sellable": True, "score": 75, "reason": "string"}
    }

    resp = client.chat.completions.create(
        model=_model(),
        temperature=0,
        messages=[
            {"role": "system", "content": "Réponds uniquement en JSON valide."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
        ]
    )

    txt = (resp.choices[0].message.content or "").strip()
    try:
        data = json.loads(txt)
        sellable = bool(data.get("sellable", False))
        score = int(data.get("score", 0) or 0)
        reason = str(data.get("reason","") or "")
        score = max(0, min(100, score))
        return {"sellable": sellable and score > 0, "score": score, "reason": reason}
    except Exception:
        return {"sellable": False, "score": 0, "reason": "json_parse_failed"}

ANALYSIS_SCHEMA = {
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

def generate_analysis(product_payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
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
        "product": product_payload
    }

    resp = client.chat.completions.create(
        model=_model(),
        temperature=0.4,
        messages=[
            {"role": "system", "content": "Réponds uniquement en JSON valide."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
        ]
    )

    txt = (resp.choices[0].message.content or "").strip()
    try:
        return json.loads(txt)
    except Exception:
        s = txt.find("{")
        e = txt.rfind("}")
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(txt[s:e+1])
            except Exception:
                pass
        return {"raw": txt, "schema": ANALYSIS_SCHEMA}