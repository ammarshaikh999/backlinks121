from urllib.parse import urlparse
import re


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(normalize_url(url))
        domain = parsed.netloc.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def get_root_domain_url(url: str) -> str:
    url = normalize_url(url)
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc
    return f"{scheme}://{netloc}/"


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_competitors(raw: str) -> list[str]:
    if not raw:
        return []
    parts = [p.strip().lower() for p in str(raw).split("|") if p.strip()]
    cleaned = []
    for part in parts:
        part = part.replace("https://", "").replace("http://", "").strip("/")
        if part.startswith("www."):
            part = part[4:]
        cleaned.append(part)
    return cleaned


def contains_any(text: str, keywords: list[str]) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def safe_bool(value, default=False):
    try:
        return bool(value)
    except Exception:
        return default
