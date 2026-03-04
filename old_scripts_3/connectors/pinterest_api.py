import os
import requests

ACCESS_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN")


def fetch_pinterest_signal(query: str):

    url = "https://api.pinterest.com/v5/pins/search"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    params = {
        "query": query,
        "page_size": 25
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)

        data = r.json()

        items = data.get("items", [])

        image_url = None

        if items:
            image_url = items[0]["media"]["images"]["orig"]["url"]

        return {
            "hits": len(items),
            "image_url": image_url,
            "source_url": f"https://www.pinterest.com/search/pins/?q={query}"
        }

    except Exception:
        return {
            "hits": 0,
            "image_url": None,
            "source_url": None
        }