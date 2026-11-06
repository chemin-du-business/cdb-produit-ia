"""Client SerpApi centralisé — clé API uniquement depuis variable d'environnement."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import requests

SERPAPI_BASE = "https://serpapi.com/search"
_DEFAULT_TIMEOUT = 30


def _get_api_key() -> str:
    key = os.environ.get("SERPAPI_KEY", "")
    if not key:
        raise EnvironmentError("SERPAPI_KEY manquante dans les variables d'environnement")
    return key


def serpapi_get(
    engine: str,
    params: Dict[str, Any],
    retries: int = 3,
    backoff: float = 2.0,
) -> Dict[str, Any]:
    """
    Appel SerpApi avec retry exponentiel.
    Retourne le JSON brut ou lève une exception.
    """
    full_params = {
        "engine": engine,
        "api_key": _get_api_key(),
        **params,
    }

    last_err: Optional[Exception] = None
    for attempt in range(retries):
        try:
            resp = requests.get(SERPAPI_BASE, params=full_params, timeout=_DEFAULT_TIMEOUT)
            # 400 = erreur permanente (mauvais params ou engine non disponible sur ce plan)
            # Inutile de retenter — on échoue immédiatement
            if resp.status_code == 400:
                raise RuntimeError(f"SerpApi {engine} 400 Bad Request (engine non disponible ou params invalides)")
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise ValueError(f"SerpApi error: {data['error']}")
            return data
        except RuntimeError:
            raise  # 400 : on ne retente pas
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))

    raise RuntimeError(f"SerpApi {engine} failed after {retries} attempts: {last_err}")
