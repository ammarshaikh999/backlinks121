import re

ALLOWED_TYPES = {
    "guest_post",
    "profile",
    "social_bookmarking",
    "web_directory",
    "article",
    "business_listing",
    "email_submission",
    "directory_business",
}

TYPE_RULES = [
    ("guest_post", [
        r"write-for-us",
        r"guest-post",
        r"submit-guest-post",
        r"contribute",
        r"become-a-contributor",
    ]),
    ("profile", [
        r"/profile",
        r"/user/",
        r"/member/",
        r"/account/",
        r"/reviews/",
        r"trustindex\.io",
    ]),
    ("social_bookmarking", [
        r"reddit\.com",
        r"pinterest\.com",
        r"tumblr\.com",
        r"mix\.com",
        r"slashdot",
    ]),
    ("web_directory", [
        r"/directory/",
        r"/category/",
        r"/listing/",
        r"/listings/",
        r"/resources/",
        r"/links/",
    ]),
    ("article", [
        r"/article/",
        r"/blog/",
        r"/news/",
        r"/stories/",
        r"/post/",
    ]),
    ("business_listing", [
        r"yellowpages",
        r"yelp\.",
        r"foursquare",
        r"hotfrog",
        r"sitejabber",
        r"trustpilot",
        r"ourblackeconomy",
        r"meetyourmarkets",
        r"sayellow",
    ]),
    ("email_submission", [
        r"newsletter",
        r"subscribe",
        r"mailing-list",
    ]),
    ("directory_business", [
        r"business-directory",
        r"/business/",
        r"/companies/",
        r"/services/",
        r"757pages",
    ]),
]

NICHE_KEYWORDS = [
    "jacket",
    "jackets",
    "leather jacket",
    "hoodie",
    "hoodies",
    "coat",
    "outerwear",
    "fashion",
    "clothing",
    "apparel",
    "streetwear",
]

NEGATIVE_KEYWORDS = [
    "real estate",
    "property",
    "broker",
    "villa",
    "apartment",
    "realty",
    "construction",
]


def classify_backlink_type(url: str, title: str = "", text: str = "") -> str:
    blob = f"{url} {title} {text}".lower()
    for backlink_type, patterns in TYPE_RULES:
        if any(re.search(p, blob) for p in patterns):
            return backlink_type
    return "needs_review"


def is_allowed_type(backlink_type: str, allowed_types: list[str]) -> bool:
    return backlink_type in set(allowed_types)


def check_niche_relevance(*parts: str) -> bool:
    text = " ".join(parts).lower()
    if any(n in text for n in NEGATIVE_KEYWORDS):
        return False
    return any(k in text for k in NICHE_KEYWORDS)
