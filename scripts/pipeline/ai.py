import os, json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"

def is_sellable_product(term: str, geo: str = "FR") -> bool:
    """
    Retourne True si le terme correspond à un PRODUIT e-commerce concret.
    Filtre people/politique/match/événement/actu.
    """
    term = (term or "").strip()
    if not term:
        return False

    resp = client.chat.completions.create(
        model=_model(),
        temperature=0,
        messages=[
            {"role": "system", "content": (
                "Réponds uniquement par OUI ou NON. "
                "OUI seulement si c'est un produit e-commerce concret vendable "
                "(objet, accessoire, équipement). "
                "NON si c'est une personne, politique, match, film, événement, score, actualité."
            )},
            {"role": "user", "content": f"Terme: {term} (marché {geo})"}
        ],
    )
    txt = (resp.choices[0].message.content or "").strip().upper()
    return txt.startswith("OUI")