from __future__ import annotations

import os
import json
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
    """
    Compatible OpenAI SDK 1.14.x: uses chat.completions.
    Returns JSON dict.
    """
    instructions = (
        "Tu es un expert e-commerce FR. "
        "Réponds UNIQUEMENT en JSON valide, sans texte autour. "
        f"Marché cible: {geo}. "
        "Tu dois produire une analyse structurée du produit potentiel. "
        "Respecte le schéma fourni (mêmes clés)."
    )

    payload = {
        "product": product,
        "schema": ANALYSIS_SCHEMA_HINT
    }

    # IMPORTANT: modèle large compat. Si tu veux moins cher, mets gpt-4o-mini
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    resp = client.chat.completions.create(
        model=model,
        temperature=0.4,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )

    text = resp.choices[0].message.content.strip()

    # Robust JSON parse
    try:
        return json.loads(text)
    except Exception:
        # Try to extract JSON if model wrapped it
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
        return {"raw": text}