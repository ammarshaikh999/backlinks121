from .utils import extract_domain, clean_text


def detect_follow_type(rel_values):
    if not rel_values:
        return "dofollow"

    if isinstance(rel_values, str):
        rel_items = rel_values.split()
    elif isinstance(rel_values, (list, tuple, set)):
        rel_items = rel_values
    else:
        rel_items = [str(rel_values)]

    rel_set = {str(r).strip().lower() for r in rel_items if str(r).strip()}

    if "sponsored" in rel_set:
        return "sponsored"
    if "ugc" in rel_set:
        return "ugc"
    if "nofollow" in rel_set:
        return "nofollow"
    return "dofollow"


def normalize_domain(value: str) -> str:
    raw = str(value or "").strip().lower()
    domain = extract_domain(raw)

    if not domain and raw:
        domain = raw.replace("http://", "").replace("https://", "").strip("/")

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def detect_competitor_presence(page_data: dict, competitor_domains: list[str]) -> dict:
    linked_competitors = set()
    mentioned_competitors = set()
    competitor_anchors = []
    follow_summary = []

    text_blob = (page_data.get("text_content") or "").lower()
    normalized_competitors = sorted(
        {normalize_domain(c) for c in competitor_domains if normalize_domain(c)}
    )

    for link in page_data.get("all_links", []):
        href_domain = normalize_domain(link.get("href", ""))
        anchor = clean_text(link.get("anchor", ""))
        rel_values = link.get("rel", []) or []
        follow_type = detect_follow_type(rel_values)

        if not href_domain:
            continue

        for comp in normalized_competitors:
            if href_domain == comp or href_domain.endswith("." + comp):
                linked_competitors.add(comp)
                follow_summary.append(follow_type)

                if anchor:
                    competitor_anchors.append(f"{anchor} ({follow_type})")

    for comp in normalized_competitors:
        if comp in text_blob:
            mentioned_competitors.add(comp)

    return {
        "competitor_linked": len(linked_competitors) > 0,
        "competitor_mentioned": len(mentioned_competitors) > 0,
        "competitor_domains_linked": sorted(linked_competitors),
        "competitor_domains_mentioned": sorted(mentioned_competitors),
        "competitor_anchor_examples": sorted(set(competitor_anchors))[:10],
        "competitor_follow_types": sorted(set(follow_summary)),
    }


def detect_page_external_follow_types(page_data: dict, page_url: str) -> dict:
    """
    Detects follow types for all external links found on the page,
    excluding self-domain links, javascript, mailto, tel, anchors.
    """
    page_domain = normalize_domain(page_url)

    external_follow_types = []
    external_link_examples = []

    for link in page_data.get("all_links", []):
        href = str(link.get("href", "") or "").strip()
        href_lower = href.lower()

        if not href:
            continue
        if href_lower.startswith("#"):
            continue
        if href_lower.startswith("javascript:"):
            continue
        if href_lower.startswith("mailto:"):
            continue
        if href_lower.startswith("tel:"):
            continue

        href_domain = normalize_domain(href)
        if not href_domain:
            continue

        # skip internal/self links
        if href_domain == page_domain or href_domain.endswith("." + page_domain):
            continue

        rel_values = link.get("rel", []) or []
        follow_type = detect_follow_type(rel_values)
        anchor = clean_text(link.get("anchor", ""))

        external_follow_types.append(follow_type)

        if anchor:
            label = f"{anchor} -> {href_domain} ({follow_type})"
        else:
            label = f"{href_domain} ({follow_type})"

        external_link_examples.append(label)

    unique_types = sorted(set(external_follow_types))

    if unique_types == ["dofollow"]:
        page_link_policy = "mostly_dofollow"
    elif unique_types == ["nofollow"]:
        page_link_policy = "mostly_nofollow"
    elif unique_types:
        page_link_policy = "mixed"
    else:
        page_link_policy = "no_external_links_found"

    return {
        "page_external_follow_types": unique_types,
        "page_external_link_examples": sorted(set(external_link_examples))[:15],
        "page_link_policy": page_link_policy,
    }


def infer_competitor_backlink_style(backlink_type: str, competitor_presence: dict) -> str:
    if competitor_presence.get("competitor_linked"):
        return f"competitor_present_as_{backlink_type}"
    if competitor_presence.get("competitor_mentioned"):
        return f"competitor_mentioned_on_{backlink_type}_page"
    return "no_competitor_pattern_found"
