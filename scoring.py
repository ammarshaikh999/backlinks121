def calculate_priority_score(
    status_code: int,
    indexable: bool,
    external_links: int,
    niche_relevant: bool,
    backlink_type: str,
    allowed_type: bool,
    competitor_linked: bool,
    extracted_keywords: list[str],
) -> int:
    score = 0

    if status_code == 200:
        score += 20
    if indexable:
        score += 15
    if niche_relevant:
        score += 20
    if allowed_type:
        score += 15
    if competitor_linked:
        score += 15

    if 1 <= external_links <= 80:
        score += 10
    elif external_links == 0:
        score += 2
    else:
        score -= 5

    if backlink_type in {"guest_post", "article"}:
        score += 5
    elif backlink_type in {"business_listing", "directory_business", "profile"}:
        score += 3

    if len(extracted_keywords) >= 5:
        score += 5

    score = max(1, min(100, score))
    return score


def priority_label(score: int, high: int = 75, medium: int = 50) -> str:
    if score >= high:
        return "high"
    if score >= medium:
        return "medium"
    return "low"
