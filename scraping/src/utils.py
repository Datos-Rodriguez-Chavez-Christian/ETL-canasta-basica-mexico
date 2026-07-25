import random
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from config import HTML_DEBUG_DIR, OUTPUT_DIR


def ensure_directories() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_text(text: str | None) -> str | None:
    if text is None:
        return None

    cleaned = " ".join(text.split()).strip()
    return cleaned or None


def build_url(base_url: str, href: str | None) -> str | None:
    if not href:
        return None

    return urljoin(base_url, href)


def normalize_price(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.replace("$", "").replace(",", "").strip()
    match = re.search(r"\d+(?:\.\d+)?", value)

    return match.group(0) if match else None


def extract_sku_from_url(url: str | None, patterns: list[str]) -> str | None:
    if not url:
        return None

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def slugify(value: str | None, default: str = "sin_nombre") -> str:
    value = clean_text(value) or default
    value = value.lower()
    value = re.sub(r"[^a-z0-9áéíóúñü]+", "_", value, flags=re.IGNORECASE)
    value = value.strip("_")

    return value or default


def random_pause(min_seconds: float, max_seconds: float) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def save_html_debug(store_key: str, category: str, subcategory: str | None, html: str, reason: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}_{slugify(store_key)}_{slugify(category)}_{slugify(subcategory)}_{slugify(reason)}.html"
    path = HTML_DEBUG_DIR / file_name
    path.write_text(html, encoding="utf-8")

    return path