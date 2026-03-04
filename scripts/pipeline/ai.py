from __future__ import annotations
import os, json
from typing import Any, Dict
from openai import OpenAI

client = OpenAI(api_key=(os.environ.get("OPENAI_API_KEY") or "").strip())

def _model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"

def _safe_json_load(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        return {}

def extract_product_name(caption: str, geo: str="FR") -> str:
    caption=(caption or "").strip()
    if not caption:
        return ""
    resp=client.chat.completions.create(
        model=_model(),
        temperature=0,
        messages=[
            {"role":"system","content":"Extrait UN SEUL nom de produit e-commerce concret depuis une caption TikTok. Réponds uniquement par le nom (2-6 mots) en FR si possible. Si aucun produit clair: RIEN."},
            {"role":"user","content":f"Caption: {caption}\nMarché: {geo}"},
        ],
    )
    txt=(resp.choices[0].message.content or "").strip()
    if txt.upper().startswith("RIEN"):
        return ""
    return txt[:80]

def is_sellable_product(term: str, geo: str="FR") -> bool:
    term=(term or "").strip()
    if not term:
        return False
    resp=client.chat.completions.create(
        model=_model(),
        temperature=0,
        messages=[
            {"role":"system","content":"Réponds uniquement par OUI ou NON. OUI seulement si c''est un produit e-commerce concret vendable (objet, accessoire, équipement). NON sinon (personne, match, événement, politique, etc)."},
            {"role":"user","content":f"Terme: {term} (marché {geo})"},
        ],
    )
    txt=(resp.choices[0].message.content or "").strip().upper()
    return txt.startswith("OUI")

def generate_analysis(payload: Dict[str, Any], geo: str="FR") -> Dict[str, Any]:
    prompt={
        "title":payload.get("title"),
        "category":payload.get("category"),
        "tags":payload.get("tags",[]),
        "sources":payload.get("sources",[]),
        "signals":payload.get("signals",{}),
        "market":geo,
        "output_schema":{
            "risks":[{"note":"...","type":"...","level":"low|medium|high"}],
            "angles":{
                "hooks":["..."],
                "objections":[{"objection":"...","response":"..."}],
                "ugc_script":{"script":"...","duration_seconds":20}
            },
            "confidence":{"score":1,"reasons":["..."]},
            "positioning":{"why_now":"...","main_promise":"...","problem_solved":"...","target_customer":"..."},
            "recommendations":{"upsells":["..."],"channels":["..."],"price_range":{"min":0,"max":0,"currency":"EUR"}}
        }
    }
    resp=client.chat.completions.create(
        model=_model(),
        temperature=0.4,
        messages=[
            {"role":"system","content":"Tu es un expert e-commerce FR. Retourne UNIQUEMENT un JSON valide (sans markdown, sans texte)."},
            {"role":"user","content":json.dumps(prompt,ensure_ascii=False)},
        ],
    )
    txt=(resp.choices[0].message.content or "").strip()
    data=_safe_json_load(txt)
    if not data:
        data={
            "risks":[{"note":"Données insuffisantes","type":"data","level":"medium"}],
            "angles":{"hooks":[],"objections":[],"ugc_script":{"script":"","duration_seconds":20}},
            "confidence":{"score":5,"reasons":["Signal TikTok"]},
            "positioning":{"why_now":"","main_promise":"","problem_solved":"","target_customer":""},
            "recommendations":{"upsells":[],"channels":[],"price_range":{"min":19,"max":49,"currency":"EUR"}}
        }
    return data
