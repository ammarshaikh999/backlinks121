# 🔗 Backlink Intelligence Pipeline

A tool to evaluate and score backlink target pages for SEO outreach.

## Project Structure

```
backlink-tool/
├── .devcontainer/
│   └── devcontainer.json       # GitHub Codespaces config
├── data/
│   └── targets.csv             # Your input URLs
├── src/
│   ├── __init__.py
│   ├── anchors.py              # Anchor text suggestions
│   ├── classify.py             # Backlink type classifier
│   ├── competitor_patterns.py  # Competitor link detection
│   ├── exporter.py             # CSV/Excel export
│   ├── fetcher.py              # Page fetcher (requests + BS4)
│   ├── keywords.py             # Keyword extractor
│   ├── main.py                 # Core pipeline logic
│   ├── moz_client.py           # Moz API client (optional)
│   ├── scoring.py              # Priority scoring
│   └── utils.py                # Shared utilities
├── app.py                      # CLI entry point
├── streamlit_app.py            # ← Streamlit web UI
├── config.yml                  # Configuration
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Run — Streamlit UI (recommended)

```bash
streamlit run streamlit_app.py
```

Then open http://localhost:8501

## Run — Command Line

```bash
python app.py
```

Reads `config.yml` and `data/targets.csv`, outputs `backlink_pipeline.xlsx`.

## targets.csv Columns

| Column        | Required | Description                              |
|---------------|----------|------------------------------------------|
| `url`         | ✅ Yes   | Target page URL to evaluate              |
| `brand`       | No       | Override brand name from config.yml      |
| `niche`       | No       | Override niche from config.yml           |
| `competitors` | No       | Pipe-separated competitor domains        |
| `notes`       | No       | Any notes about this URL                 |

Example:
```
url,brand,niche,competitors,notes
https://example.com/blog,My Brand,fashion jackets,comp1.com|comp2.com,guest post opportunity
```

## Scoring Logic

| Factor                   | Points |
|--------------------------|--------|
| Status 200               | +20    |
| Indexable                | +15    |
| Niche relevant           | +20    |
| Allowed backlink type    | +15    |
| Competitor linked        | +15    |
| External links 1–80      | +10    |
| Guest post / article     | +5     |
| 5+ keywords extracted    | +5     |

Score ≥ 75 = **High** | Score ≥ 50 = **Medium** | Score < 50 = **Low**

## Action Logic

- `reject` — backlink type not in allowed list
- `qualified` — allowed type + niche relevant + score ≥ 50
- `needs_review` — everything else
