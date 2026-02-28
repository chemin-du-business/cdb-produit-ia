from __future__ import annotations
import os
from typing import Any, Dict
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

ANALYSIS_SCHEMA_HINT = {
    "positioning": {
        "main_promise": "string",
        "target_customer": "string",
        "problem_solved": "string",
        "why_now": "string"
    },
    "angles": {
        "hooks": ["string", "string", "string"],
        "objections": [{"objection": "string", "response": "string"}],
        "ugc_script": {"script": "string", "duration_seconds": 20}
    },
    "risks": [{"type": "string", "level": "low|medium|high", "note": "string"}],
    "recommendations": {
        "price_range": {"min": 0, "max": 0, "currency": "EUR"},
        "channels": ["string"],
        "upsells": ["string"]
    },
    "confidence": {"score": 0, "reasons": ["string"]}
}

def generate_analysis(product: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    title = product["title"]
    category = product.get("category", "autre")
    tags = product.get("tags", [])
    sources = product.get("sources", [])
    signals = product.get("signals", {})

    instructions = (
        "Tu es un expert e-commerce FR. Tu dois produire une analyse structurée JSON uniquement "
        "pour un produit potentiel. Pas de texte hors JSON.\n"
        f"Le marché cible est {geo}. Sois concret, orienté ads et page produit.\n"
        "Respecte ce schéma (clés identiques) et remplis proprement."
    )

    user_input = {
        "product": {
            "title": title,
            "category": category,
            "tags": tags,
            "sources": sources,
            "signals": signals
        },
        "schema": ANALYSIS_SCHEMA_HINT
    }

    resp = client.responses.create(
        model="gpt-5.2",
        input=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": str(user_input)},
        ],
        reasoning={"effort": "low"},
    )
    text = resp.output_text.strip()

    # robuste: si le modèle renvoie du JSON en texte
    import json
    try:
        return json.loads(text)
    except Exception:
        # fallback minimal
        return {"raw": text}