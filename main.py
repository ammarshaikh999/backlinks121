import yaml
import pandas as pd
from datetime import datetime

from .utils import normalize_url, extract_domain, split_competitors, get_root_domain_url
from .fetcher import fetch_page
from .classify import classify_backlink_type, is_allowed_type, check_niche_relevance
from .competitor_patterns import detect_competitor_presence, detect_page_external_follow_types, infer_competitor_backlink_style
from .keywords import extract_keywords
from .anchors import suggest_anchor_texts
from .scoring import calculate_priority_score, priority_label
from .exporter import export_csv, export_xlsx


def evaluate_page(
    url: str,
    brand: str,
    row_niche: str,
    notes: str,
    competitor_domains: list[str],
    allowed_types: list[str],
    timeout: int,
    user_agent: str,
    config: dict,
):
    page = fetch_page(url, timeout=timeout, user_agent=user_agent)

    final_url = page.get("final_url", "") or url
    final_domain = extract_domain(final_url)

    backlink_type = classify_backlink_type(
        url=final_url,
        title=page.get("title", ""),
        text=page.get("text_content", "")[:5000],
    )

    allowed_type = is_allowed_type(backlink_type, allowed_types)

    niche_relevant = check_niche_relevance(
        page.get("title", ""),
        page.get("meta_description", ""),
        page.get("h1", ""),
        page.get("text_content", "")[:5000],
    )

    # Override: real-estate URLs are never niche-relevant for fashion
    if "real-estate" in final_url.lower():
        niche_relevant = False

    competitor_presence = detect_competitor_presence(page, competitor_domains)
    competitor_style = infer_competitor_backlink_style(backlink_type, competitor_presence)

    keywords = extract_keywords(
        title=page.get("title", ""),
        meta_description=page.get("meta_description", ""),
        h1=page.get("h1", ""),
        text_content=page.get("text_content", ""),
        top_n=12,
    )

    anchor_suggestions = suggest_anchor_texts(
        brand_name=brand,
        niche=row_niche,
        backlink_type=backlink_type,
        extracted_keywords=keywords,
    )

    score = calculate_priority_score(
        status_code=page.get("status_code", 0),
        indexable=page.get("indexable", False),
        external_links=page.get("external_links", 0),
        niche_relevant=niche_relevant,
        backlink_type=backlink_type,
        allowed_type=allowed_type,
        competitor_linked=competitor_presence.get("competitor_linked", False),
        extracted_keywords=keywords,
    )

    label = priority_label(
        score,
        high=config.get("priority_thresholds", {}).get("high", 75),
        medium=config.get("priority_thresholds", {}).get("medium", 50),
    )

    page_follow_data = detect_page_external_follow_types(page, final_url)

    # BUG FIX: original had `score >= 50` but score is already clamped 1–100,
    # and allowed_type + niche_relevant are the right gates. Keep consistent.
    if not allowed_type:
        action = "reject"
    elif allowed_type and niche_relevant and score >= 50:
        action = "qualified"
    else:
        action = "needs_review"

    return {
        "checked_url": url,
        "checked_domain": final_domain,
        "final_url": final_url,
        "status_code": page.get("status_code", 0),
        "indexable": page.get("indexable", False),
        "page_title": page.get("title", ""),
        "meta_description": page.get("meta_description", ""),
        "h1": page.get("h1", ""),
        "backlink_type": backlink_type,
        "allowed_type": allowed_type,
        "niche_relevant": niche_relevant,
        "internal_links": page.get("internal_links", 0),
        "external_links": page.get("external_links", 0),
        "competitor_linked": competitor_presence.get("competitor_linked", False),
        "competitor_mentioned": competitor_presence.get("competitor_mentioned", False),
        "competitor_domains_linked": competitor_presence.get("competitor_domains_linked", []),
        "competitor_domains_mentioned": competitor_presence.get("competitor_domains_mentioned", []),
        "competitor_anchor_examples": competitor_presence.get("competitor_anchor_examples", []),
        "page_external_follow_types": page_follow_data.get("page_external_follow_types", []),
        "page_external_link_examples": page_follow_data.get("page_external_link_examples", []),
        "page_link_policy": page_follow_data.get("page_link_policy", "unknown"),
        "competitor_backlink_style": competitor_style,
        "extracted_keywords": keywords,
        "anchor_text_suggestions": anchor_suggestions,
        "priority_score": score,
        "priority_label": label,
        "action": action,
        "error": page.get("error", ""),
    }


def merge_unique_lists(a, b):
    return sorted(set((a or []) + (b or [])))


def choose_final_action(page_result: dict, domain_result: dict) -> str:
    if page_result["action"] == "reject":
        return "reject"
    if page_result["action"] == "qualified" and domain_result["action"] != "reject":
        return "qualified"
    return "needs_review"


def choose_final_score(page_result: dict, domain_result: dict) -> int:
    return max(page_result["priority_score"], domain_result["priority_score"])


def choose_final_label(page_result: dict, domain_result: dict) -> str:
    if page_result["priority_score"] >= domain_result["priority_score"]:
        return page_result["priority_label"]
    return domain_result["priority_label"]


def run_pipeline():
    with open("config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    df = pd.read_csv("data/targets.csv")

    if "url" not in df.columns:
        raise ValueError("targets.csv must contain a 'url' column")

    df["url"] = df["url"].astype(str).apply(normalize_url)
    df["domain"] = df["url"].apply(extract_domain)
    df["sno"] = range(1, len(df) + 1)

    brand_name = config.get("brand_name", "")
    niche = config.get("niche", "")
    allowed_types = config.get("allowed_backlink_types", [])

    timeout = config.get("request", {}).get("timeout_seconds", 20)
    user_agent = config.get("request", {}).get("user_agent", "Mozilla/5.0")

    processed_date = datetime.utcnow().strftime("%Y-%m-%d")

    rows = []

    for _, row in df.iterrows():
        url = row.get("url", "")
        brand = row.get("brand", brand_name)
        row_niche = row.get("niche", niche)
        notes = row.get("notes", "")
        competitor_domains = split_competitors(row.get("competitors", ""))

        page_result = evaluate_page(
            url=url,
            brand=brand,
            row_niche=row_niche,
            notes=notes,
            competitor_domains=competitor_domains,
            allowed_types=allowed_types,
            timeout=timeout,
            user_agent=user_agent,
            config=config,
        )

        root_url = get_root_domain_url(page_result["final_url"] or url)

        domain_result = evaluate_page(
            url=root_url,
            brand=brand,
            row_niche=row_niche,
            notes=notes,
            competitor_domains=competitor_domains,
            allowed_types=allowed_types,
            timeout=timeout,
            user_agent=user_agent,
            config=config,
        )

        combined_action = choose_final_action(page_result, domain_result)
        combined_score  = choose_final_score(page_result, domain_result)
        combined_label  = choose_final_label(page_result, domain_result)

        rows.append({
            "sno": row.get("sno"),
            "processed_date": processed_date,
            "brand": brand,
            "niche": row_niche,
            "source_url": url,
            "source_domain": extract_domain(url),

            "target_page_url": page_result["checked_url"],
            "target_page_final_url": page_result["final_url"],
            "target_page_status_code": page_result["status_code"],
            "target_page_indexable": page_result["indexable"],
            "target_page_title": page_result["page_title"],
            "target_page_meta_description": page_result["meta_description"],
            "target_page_h1": page_result["h1"],
            "target_page_backlink_type": page_result["backlink_type"],
            "target_page_allowed_type": page_result["allowed_type"],
            "target_page_niche_relevant": page_result["niche_relevant"],
            "target_page_internal_links": page_result["internal_links"],
            "target_page_external_links": page_result["external_links"],
            "target_page_priority_score": page_result["priority_score"],
            "target_page_priority_label": page_result["priority_label"],
            "target_page_action": page_result["action"],

            "domain_url": domain_result["checked_url"],
            "domain_final_url": domain_result["final_url"],
            "domain_status_code": domain_result["status_code"],
            "domain_indexable": domain_result["indexable"],
            "domain_title": domain_result["page_title"],
            "domain_meta_description": domain_result["meta_description"],
            "domain_h1": domain_result["h1"],
            "domain_backlink_type": domain_result["backlink_type"],
            "domain_allowed_type": domain_result["allowed_type"],
            "domain_niche_relevant": domain_result["niche_relevant"],
            "domain_internal_links": domain_result["internal_links"],
            "domain_external_links": domain_result["external_links"],
            "domain_priority_score": domain_result["priority_score"],
            "domain_priority_label": domain_result["priority_label"],
            "domain_action": domain_result["action"],

            "competitor_domains_input": " | ".join(competitor_domains),
            "competitor_linked": page_result["competitor_linked"] or domain_result["competitor_linked"],
            "competitor_mentioned": page_result["competitor_mentioned"] or domain_result["competitor_mentioned"],
            "competitor_domains_linked": " | ".join(
                merge_unique_lists(
                    page_result["competitor_domains_linked"],
                    domain_result["competitor_domains_linked"],
                )
            ),
            "competitor_domains_mentioned": " | ".join(
                merge_unique_lists(
                    page_result["competitor_domains_mentioned"],
                    domain_result["competitor_domains_mentioned"],
                )
            ),
            "competitor_anchor_examples": " | ".join(
                merge_unique_lists(
                    page_result["competitor_anchor_examples"],
                    domain_result["competitor_anchor_examples"],
                )[:10]
            ),

            "target_page_external_follow_types": " | ".join(page_result.get("page_external_follow_types", [])) or "none",
            "domain_external_follow_types": " | ".join(domain_result.get("page_external_follow_types", [])) or "none",

            "target_page_link_policy": page_result.get("page_link_policy", "unknown"),
            "domain_link_policy": domain_result.get("page_link_policy", "unknown"),

            "target_page_external_link_examples": " | ".join(page_result.get("page_external_link_examples", [])[:10]),
            "domain_external_link_examples": " | ".join(domain_result.get("page_external_link_examples", [])[:10]),

            "target_page_competitor_backlink_style": page_result["competitor_backlink_style"],
            "domain_competitor_backlink_style": domain_result["competitor_backlink_style"],

            "target_page_extracted_keywords": " | ".join(page_result["extracted_keywords"]),
            "domain_extracted_keywords": " | ".join(domain_result["extracted_keywords"]),

            "target_page_anchor_text_suggestions": " | ".join(page_result["anchor_text_suggestions"]),
            "domain_anchor_text_suggestions": " | ".join(domain_result["anchor_text_suggestions"]),

            "priority_score": combined_score,
            "priority_label": combined_label,
            "action": combined_action,
            "notes": notes,
            "error": " | ".join(filter(None, [page_result["error"], domain_result["error"]])),
        })

    out = pd.DataFrame(rows)

    xlsx_path = config.get("output", {}).get("xlsx_file", "backlink_pipeline.xlsx")

    qualified = out[out["action"] == "qualified"].copy()
    review    = out[out["action"] == "needs_review"].copy()
    rejected  = out[out["action"] == "reject"].copy()

    export_xlsx(
        {
            "AllTargets": out,
            "Qualified": qualified,
            "NeedsReview": review,
            "Rejected": rejected,
        },
        xlsx_path,
    )

    print(f"Done. Excel created: {xlsx_path}")
    print(f"Processed: {len(out)}")
    print(f"Qualified: {len(qualified)}")
    print(f"Needs review: {len(review)}")
    print(f"Rejected: {len(rejected)}")
