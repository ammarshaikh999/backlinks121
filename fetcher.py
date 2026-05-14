import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .utils import clean_text, extract_domain


def fetch_page(url: str, timeout: int = 20, user_agent: str = "Mozilla/5.0") -> dict:
    result = {
        "final_url": url,
        "status_code": 0,
        "html": "",
        "title": "",
        "meta_description": "",
        "h1": "",
        "indexable": False,
        "canonical": "",
        "internal_links": 0,
        "external_links": 0,
        "all_links": [],
        "text_content": "",
        "error": "",
    }
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        result["final_url"] = response.url
        result["status_code"] = response.status_code

        if response.status_code != 200:
            return result

        html = response.text
        result["html"] = html
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find("title")
        result["title"] = clean_text(title_tag.get_text(" ")) if title_tag else ""

        meta_desc = soup.find("meta", attrs={"name": "description"})
        result["meta_description"] = clean_text(meta_desc.get("content", "")) if meta_desc else ""

        h1_tag = soup.find("h1")
        result["h1"] = clean_text(h1_tag.get_text(" ")) if h1_tag else ""

        robots = soup.find("meta", attrs={"name": "robots"})
        robots_content = (robots.get("content", "") if robots else "").lower()
        result["indexable"] = "noindex" not in robots_content

        canonical = soup.find("link", attrs={"rel": "canonical"})
        result["canonical"] = canonical.get("href", "").strip() if canonical else ""

        current_domain = extract_domain(response.url)
        links = []
        internal_links = 0
        external_links = 0

        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if not href:
                continue
            absolute = urljoin(response.url, href)
            anchor = clean_text(a.get_text(" "))
            domain = extract_domain(absolute)

            if domain and domain == current_domain:
                internal_links += 1
            elif domain:
                external_links += 1

            rel_attr = a.get("rel", [])
            rel_values = [r.lower() for r in rel_attr] if rel_attr else []
            links.append({
                "href": absolute,
                "domain": domain,
                "anchor": anchor,
                "rel": rel_values,
            })

        result["all_links"] = links
        result["internal_links"] = internal_links
        result["external_links"] = external_links

        body_text = soup.get_text(" ", strip=True)
        result["text_content"] = clean_text(body_text)[:15000]

    except Exception as e:
        result["error"] = str(e)

    return result
