import re
from collections import Counter

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "into", "are", "was",
    "have", "has", "had", "you", "our", "not", "but", "can", "all", "out", "about",
    "business", "page", "home", "contact", "privacy", "terms", "login", "sign", "submit",
    "directory", "listing", "article", "blog", "post", "write", "guest", "profile",
    "review", "reviews", "more", "read", "shop", "store",
}


def tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    words = re.findall(r"[a-z][a-z0-9\-]{2,}", text)
    return [w for w in words if w not in STOPWORDS]


def extract_keywords(
    title: str,
    meta_description: str,
    h1: str,
    text_content: str,
    top_n: int = 12,
) -> list[str]:
    weighted_terms = []
    weighted_terms.extend(tokenize(title) * 4)
    weighted_terms.extend(tokenize(h1) * 3)
    weighted_terms.extend(tokenize(meta_description) * 2)
    weighted_terms.extend(tokenize(text_content)[:500])

    counts = Counter(weighted_terms)
    keywords = [term for term, _ in counts.most_common(top_n)]
    return keywords
