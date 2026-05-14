def suggest_anchor_texts(
    brand_name: str,
    niche: str,
    backlink_type: str,
    extracted_keywords: list[str],
) -> list[str]:
    brand = (brand_name or "").strip()
    niche = (niche or "").strip()

    generic = [
        brand,
        f"{brand} official store",
        f"{brand} jackets",
        f"{brand} outerwear",
        f"shop {brand}",
    ]

    niche_based = [
        "celebrity jackets",
        "leather jackets",
        "men jackets",
        "women jackets",
        "fashion outerwear",
    ]

    contextual = []
    for kw in extracted_keywords[:5]:
        contextual.append(f"{brand} {kw}")
        contextual.append(kw)

    if backlink_type == "guest_post":
        contextual.extend([
            f"{brand} style guide",
            f"{brand} fashion collection",
        ])
    elif backlink_type in {"business_listing", "directory_business", "profile"}:
        contextual.extend([
            brand,
            f"{brand} official website",
            f"{brand} online store",
        ])

    seen = set()
    result = []
    for anchor in generic + niche_based + contextual:
        a = " ".join(anchor.split()).strip()
        if not a or a.lower() in seen:
            continue
        seen.add(a.lower())
        result.append(a)

    return result[:10]
