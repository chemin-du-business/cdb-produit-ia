import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def _model() -> str:
    # Si OPENAI_MODEL est vide, fallback
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"


# Mots trop génériques -> pas un "produit" exploitable
_GENERIC_BLACKLIST = [
    "accessoire", "accessoires",
    "produit", "produits",
    "objet", "objets",
    "article", "articles",
    "équipement", "equipement",
    "matériel", "materiel",
    "idée", "idee",
]


def is_sellable_product(term: str, geo: str = "FR") -> bool:
    """
    Filtre: garde uniquement les termes qui ressemblent à un produit e-commerce concret.
    1) filtre local (mots trop génériques)
    2) filtre IA OUI/NON (évite people/politique/match/actu)
    """
    term = (term or "").strip()
    if not term:
        return False

    lower = term.lower()
    # filtre générique
    for w in _GENERIC_BLACKLIST:
        if w in lower and len(lower.split()) <= 4:
            return False

    try:
        resp = client.chat.completions.create(
            model=_model(),
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Réponds uniquement par OUI ou NON.\n"
                        "OUI seulement si c'est un produit e-commerce concret vendable (objet/accessoire précis).\n"
                        "NON si c'est une personne, politique, match, film, événement, score, actualité, ou trop générique."
                    ),
                },
                {"role": "user", "content": f"Terme: {term} (marché {geo})"},
            ],
        )
        txt = (resp.choices[0].message.content or "").strip().upper()
        return txt.startswith("OUI")
    except Exception as e:
        print("AI filter error:", e)
        return False


def _extract_json(text: str) -> dict:
    """
    Tente de parser un JSON. Si l'IA ajoute du texte autour, on extrait le bloc {...}.
    """
    text = (text or "").strip()
    if not text:
        return {}

    # 1) direct
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) extraction bloc
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass

    return {"raw": text}


def generate_analysis(product: dict, geo: str = "FR") -> dict:
    """
    Retourne exactement le JSON structuré demandé.
    product attendu: {
      title, category, tags, sources, signals
    }
    """
    title = (product.get("title") or "").strip()
    if not title:
        return {}

    category = (product.get("category") or "autre").strip()
    tags = product.get("tags") or []
    sources = product.get("sources") or []
    signals = product.get("signals") or {}

    schema_example = {
        "risks": [{"note": "string", "type": "string", "level": "low|medium|high"}],
        "angles": {
            "hooks": ["string", "string"],
            "objections": [{"objection": "string", "response": "string"}],
            "ugc_script": {"script": "string", "duration_seconds": 20},
        },
        "confidence": {"score": 0, "reasons": ["string", "string"]},
        "positioning": {
            "why_now": "string",
            "main_promise": "string",
            "problem_solved": "string",
            "target_customer": "string",
        },
        "recommendations": {
            "upsells": ["string"],
            "channels": ["string"],
            "price_range": {"max": 49, "min": 29, "currency": "EUR"},
        },
    }

    instructions = (
        "Tu es un expert e-commerce FR spécialisé produits viraux.\n"
        "IMPORTANT: Tu dois répondre UNIQUEMENT en JSON valide, sans texte autour.\n"
        "Respecte exactement ces clés et sous-clés:\n"
        "- risks (liste d'objets {note,type,level})\n"
        "- angles.hooks (liste)\n"
        "- angles.objections (liste d'objets {objection,response})\n"
        "- angles.ugc_script {script,duration_seconds}\n"
        "- confidence {score (0-10), reasons (liste)}\n"
        "- positioning {why_now, main_promise, problem_solved, target_customer}\n"
        "- recommendations {upsells, channels, price_range {min,max,currency='EUR'}}\n"
        "Contraintes:\n"
        "- hooks: 2 à 4 hooks courts\n"
        "- objections: 1 à 3 objections\n"
        "- ugc_script: 15 à 25 secondes\n"
        "- confidence.score: entier 0..10\n"
        "- price_range: min<max, en EUR\n"
        f"Marché: {geo}\n"
    )

    payload = {
        "product": {
            "title": title,
            "category": category,
            "tags": tags,
            "sources": sources,
            "signals": signals,
        },
        "schema_example": schema_example,
    }

    try:
        resp = client.chat.completions.create(
            model=_model(),
            temperature=0.5,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        text = resp.choices[0].message.content or ""
        data = _extract_json(text)

        # garde-fous minimes
        if "confidence" in data and isinstance(data["confidence"], dict):
            cs = data["confidence"].get("score", 0)
            try:
                data["confidence"]["score"] = int(cs)
            except Exception:
                data["confidence"]["score"] = 0

        return data
    except Exception as e:
        print("AI analysis error:", e)
        return {}