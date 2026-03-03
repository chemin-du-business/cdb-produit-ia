import os
from openai import OpenAI

# Initialise le client OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def _model() -> str:
    """
    Retourne le modèle OpenAI configuré
    """
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"


def is_sellable_product(term: str, geo: str = "FR") -> bool:
    """
    Vérifie si le terme correspond à un produit e-commerce vendable
    (filtre personnes, politique, événements, films, etc.)
    """

    term = (term or "").strip()

    if not term:
        return False

    try:
        resp = client.chat.completions.create(
            model=_model(),
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Réponds uniquement par OUI ou NON. "
                        "OUI seulement si c'est un PRODUIT e-commerce concret "
                        "(objet, accessoire, équipement). "
                        "NON si c'est une personne, match, politique, film, événement, score ou actualité."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Terme : {term} (marché {geo})",
                },
            ],
        )

        txt = (resp.choices[0].message.content or "").strip().upper()

        return txt.startswith("OUI")

    except Exception as e:
        print("AI filter error:", e)
        return False


def generate_analysis(data: dict, geo: str = "FR") -> dict:
    """
    Génère une analyse marketing e-commerce pour un produit
    """

    title = data.get("title", "")

    if not title:
        return {}

    try:
        resp = client.chat.completions.create(
            model=_model(),
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert e-commerce spécialisé dans les produits viraux."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
Analyse ce produit pour un vendeur e-commerce.

Produit : {title}

Donne :

1. Promesse principale
2. Pourquoi ce produit peut devenir viral
3. Angle marketing
4. Cible client
5. Prix recommandé
""",
                },
            ],
        )

        text = resp.choices[0].message.content

        return {
            "analysis_text": text
        }

    except Exception as e:
        print("AI analysis error:", e)
        return {}