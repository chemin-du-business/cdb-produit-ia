from __future__ import annotations

import json
import os
from typing import Any, Dict

from openai import OpenAI


client = OpenAI(api_key=(os.environ.get("OPENAI_API_KEY") or "").strip())


def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"


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
                    "Réponds uniquement par OUI ou NON.\n"
                    "OUI uniquement si c'est un produit e-commerce concret vendable (objet, accessoire, équipement).\n"
                    "NON si c'est une personne, politique, match, film, événement, score, actualité, jeu de mots, requête SEO.\n"
                ),
            },
            {"role": "user", "content": f"Terme: {term} (marché {geo})"},
        ],
    )
    txt = (resp.choices[0].message.content or "").strip().upper()
    return txt.startswith("OUI")


def generate_analysis(payload: Dict[str, Any], geo: str = "FR") -> Dict[str, Any]:
    title = (payload.get("title") or "").strip()
    category = payload.get("category") or "autre"
    tags = payload.get("tags") or []
    sources = payload.get("sources") or []
    signals = payload.get("signals") or {}

    schema_hint = {
        "risks": [{"note": "…", "type": "Concurrence", "level": "low|medium|high"}],
        "angles": {
            "hooks": ["…", "…"],
            "objections": [{"objection": "…", "response": "…"}],
            "ugc_script": {"script": "…", "duration_seconds": 20},
        },
        "confidence": {"score": 1, "reasons": ["…"]},
        "positioning": {
            "why_now": "…",
            "main_promise": "…",
            "problem_solved": "…",
            "target_customer": "…",
        },
        "recommendations": {
            "upsells": ["…"],
            "channels": ["TikTok Ads", "UGC", "Influence"],
            "price_range": {"min": 0, "max": 0, "currency": "EUR"},
        },
    }

    resp = client.chat.completions.create(
        model=_model(),
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un expert e-commerce et marketing direct.\n"
                    "Tu dois répondre UNIQUEMENT avec un JSON valide (pas de markdown, pas de texte autour).\n"
                    "Langue: français.\n"
                    "Respecte exactement la structure demandée.\n"
                    "N'invente pas de stats chiffrées non présentes; utilise plutôt des formulations prudentes.\n"
                    "Le score confidence.score doit être entre 1 et 10.\n"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "market": geo,
                        "title": title,
                        "category": category,
                        "tags": tags,
                        "sources": sources,
                        "signals": signals,
                        "expected_schema": schema_hint,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    )

    txt = (resp.choices[0].message.content or "").strip()

    try:
        data = json.loads(txt)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {
            "risks": [{"note": "Données insuffisantes", "type": "données", "level": "medium"}],
            "angles": {"hooks": [], "objections": [], "ugc_script": {"script": "", "duration_seconds": 20}},
            "confidence": {"score": 5, "reasons": ["Analyse fallback"]},
            "positioning": {"why_now": "", "main_promise": "", "problem_solved": "", "target_customer": ""},
            "recommendations": {"upsells": [], "channels": [], "price_range": {"min": 0, "max": 0, "currency": "EUR"}},
        }
