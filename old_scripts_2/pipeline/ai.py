import os
import json
from typing import Any, Dict

from openai import OpenAI


def _client() -> OpenAI:
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def classify_product_gate(title: str, signals: Dict[str, Any]) -> Dict[str, Any]:
    model = os.environ.get("OPENAI_MODEL")
    if not model:
        return {"ok": False, "error": "Missing OPENAI_MODEL"}

    prompt = {
        "title": title,
        "signals": signals,
        "task": "Decide if this is a sellable e-commerce product idea (not politics/news/sports/person). If yes return category+tags.",
        "output_format": {
            "is_product": "boolean",
            "category": "string (beauty, home, kitchen, fitness, pets, baby, office, car, fashion, electronics, other)",
            "tags": "array of short strings",
            "reason": "short string",
        },
        "rules": [
            "Reject if it is a person, politician, match, sport event, news topic, or generic non-product query",
            "Prefer tangible product terms",
        ],
    }

    resp = _client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a strict e-commerce product gatekeeper. Output ONLY valid JSON."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
        data["ok"] = True
        return data
    except Exception:
        return {"ok": False, "error": "Invalid JSON from model", "raw": content}


def generate_analysis_json(item: Dict[str, Any]) -> Dict[str, Any]:
    model = os.environ.get("OPENAI_MODEL")
    if not model:
        return {"summary": "", "error": "Missing OPENAI_MODEL"}

    title = item.get("title", "")
    category = item.get("category", "autre")
    score = item.get("score", 0)
    signals = item.get("signals", {})
    breakdown = item.get("score_breakdown", {})

    spec = {
        "title": title,
        "category": category,
        "score": score,
        "signals": signals,
        "score_breakdown": breakdown,
        "ui_sections_required": [
            "positionnement (promesse, cible, problème résolu, pourquoi maintenant)",
            "angles_hooks (2 hooks)",
            "objections (1 objection + réponse)",
            "risques (1 risque + niveau low/medium/high)",
            "recommandations (prix conseillé, canaux, upsells)",
            "confiance (score 1-10 + 2 raisons)",
            "script_ugc_court (texte ~20s)",
        ],
        "output_format_json": {
            "summary": "string",
            "positionnement": {
                "promesse": "string",
                "cible": "string",
                "probleme_resolu": "string",
                "pourquoi_maintenant": "string",
            },
            "angles_hooks": ["string", "string"],
            "objections": {"objection": "string", "reponse": "string"},
            "risques": {"risque": "string", "niveau": "low|medium|high"},
            "recommandations": {
                "prix_conseille": "string",
                "canaux": ["string"],
                "upsells": ["string"],
            },
            "confiance": {"score": "1-10 integer", "raisons": ["string", "string"]},
            "script_ugc_court": {"texte": "string", "duree": "string"},
            "source_url": "string or null",
        },
    }

    resp = _client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an e-commerce product analyst. Output ONLY valid JSON."},
            {"role": "user", "content": json.dumps(spec, ensure_ascii=False)},
        ],
        temperature=0.5,
    )

    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except Exception:
        return {"summary": "", "error": "Invalid JSON from model", "raw": content}