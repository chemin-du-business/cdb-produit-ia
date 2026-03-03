from datetime import datetime, timezone
from slugify import slugify


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_slug(text: str) -> str:
    return slugify(text, lowercase=True, max_length=80)


def safe_int(x, default=0) -> int:
    try:
        return int(x)
    except Exception:
        return default