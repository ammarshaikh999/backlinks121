import sys
import os
import traceback

# ── PATH SETUP — must be FIRST before any other import ──────────────────────
_THIS_FILE = os.path.abspath(__file__)
_ROOT = os.path.dirname(_THIS_FILE)          # project root (where src/ lives)

# Force working directory to project root (Streamlit Cloud needs this)
os.chdir(_ROOT)

# Add root to sys.path so `import src.xxx` works
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Now safe to import Streamlit and everything else ────────────────────────
import streamlit as st
import pandas as pd
import io
from datetime import datetime

# ── Pre-flight: try importing pipeline modules and capture any error ─────────
_IMPORT_ERROR = None
try:
    from src.utils import normalize_url, extract_domain, split_competitors, get_root_domain_url
    from src.main  import (evaluate_page, merge_unique_lists,
                           choose_final_action, choose_final_score, choose_final_label)
except Exception:
    _IMPORT_ERROR = traceback.format_exc()

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Backlink Pipeline",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #0e0e0e; color: #f0f0f0; }
[data-testid="stSidebar"] { background-color: #141414; border-right: 2px solid #2a2a2a; }
.main-header { font-family:'Space Mono',monospace; font-size:2rem; font-weight:700; color:#c8f135; letter-spacing:-1px; margin-bottom:0.2rem; }
.sub-header  { font-size:0.85rem; color:#666; letter-spacing:2px; text-transform:uppercase; margin-bottom:2rem; }
.metric-card { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:4px; padding:1rem 1.2rem; text-align:center; }
.metric-card .value { font-family:'Space Mono',monospace; font-size:2rem; font-weight:700; color:#c8f135; }
.metric-card .label { font-size:0.75rem; color:#888; text-transform:uppercase; letter-spacing:1px; }
.stButton > button { background:#c8f135 !important; color:#0e0e0e !important; border:none !important; border-radius:3px !important; font-family:'Space Mono',monospace !important; font-weight:700 !important; letter-spacing:1px !important; padding:0.6rem 1.5rem !important; }
.stButton > button:hover { background:#b0d420 !important; transform:translateY(-1px) !important; }
.stTextInput > div > div > input, .stNumberInput > div > div > input, .stTextArea > div > div > textarea { background:#1a1a1a !important; border:1px solid #333 !important; color:#f0f0f0 !important; border-radius:3px !important; }
.stMultiSelect > div > div { background:#1a1a1a !important; border:1px solid #333 !important; border-radius:3px !important; }
.stSelectbox > div > div  { background:#1a1a1a !important; border:1px solid #333 !important; border-radius:3px !important; }
[data-testid="stFileUploader"] { background:#1a1a1a !important; border:1px dashed #333 !important; border-radius:4px !important; }
.stTabs [data-baseweb="tab-list"] { background-color:#141414 !important; border-bottom:1px solid #2a2a2a !important; }
.stTabs [data-baseweb="tab"] { background-color:transparent !important; color:#888 !important; font-family:'Space Mono',monospace !important; font-size:0.8rem !important; border-radius:0 !important; }
.stTabs [aria-selected="true"] { background-color:#1a1a1a !important; color:#c8f135 !important; border-bottom:2px solid #c8f135 !important; }
hr { border-color:#2a2a2a !important; }
.stProgress > div > div > div > div { background-color:#c8f135 !important; }
label { color:#aaa !important; font-size:0.82rem !important; }
</style>
""", unsafe_allow_html=True)

# ─── Process one CSV row ─────────────────────────────────────────────────────
def run_row(row, brand_name, niche, allowed_types, timeout, user_agent, config):
    url            = normalize_url(str(row.get("url", "")).strip())
    brand          = str(row.get("brand", brand_name)).strip() or brand_name
    row_niche      = str(row.get("niche",  niche)).strip()     or niche
    notes          = str(row.get("notes",  "")).strip()
    comp_domains   = split_competitors(str(row.get("competitors", "")).strip())

    pg = evaluate_page(url=url, brand=brand, row_niche=row_niche, notes=notes,
                       competitor_domains=comp_domains, allowed_types=allowed_types,
                       timeout=timeout, user_agent=user_agent, config=config)

    root_url = get_root_domain_url(pg["final_url"] or url)

    dm = evaluate_page(url=root_url, brand=brand, row_niche=row_niche, notes=notes,
                       competitor_domains=comp_domains, allowed_types=allowed_types,
                       timeout=timeout, user_agent=user_agent, config=config)

    return {
        "processed_date"  : datetime.utcnow().strftime("%Y-%m-%d"),
        "brand"           : brand,
        "niche"           : row_niche,
        "source_url"      : url,
        "source_domain"   : extract_domain(url),

        "target_page_url"             : pg["checked_url"],
        "target_page_final_url"       : pg["final_url"],
        "target_page_status_code"     : pg["status_code"],
        "target_page_indexable"       : pg["indexable"],
        "target_page_title"           : pg["page_title"],
        "target_page_meta_description": pg["meta_description"],
        "target_page_h1"              : pg["h1"],
        "target_page_backlink_type"   : pg["backlink_type"],
        "target_page_allowed_type"    : pg["allowed_type"],
        "target_page_niche_relevant"  : pg["niche_relevant"],
        "target_page_internal_links"  : pg["internal_links"],
        "target_page_external_links"  : pg["external_links"],
        "target_page_priority_score"  : pg["priority_score"],
        "target_page_priority_label"  : pg["priority_label"],
        "target_page_action"          : pg["action"],

        "domain_url"           : dm["checked_url"],
        "domain_status_code"   : dm["status_code"],
        "domain_indexable"     : dm["indexable"],
        "domain_title"         : dm["page_title"],
        "domain_backlink_type" : dm["backlink_type"],
        "domain_allowed_type"  : dm["allowed_type"],
        "domain_niche_relevant": dm["niche_relevant"],
        "domain_internal_links": dm["internal_links"],
        "domain_external_links": dm["external_links"],
        "domain_priority_score": dm["priority_score"],
        "domain_priority_label": dm["priority_label"],
        "domain_action"        : dm["action"],

        "competitor_domains_input"   : " | ".join(comp_domains),
        "competitor_linked"          : pg["competitor_linked"]   or dm["competitor_linked"],
        "competitor_mentioned"       : pg["competitor_mentioned"] or dm["competitor_mentioned"],
        "competitor_domains_linked"  : " | ".join(merge_unique_lists(pg["competitor_domains_linked"],   dm["competitor_domains_linked"])),
        "competitor_domains_mentioned": " | ".join(merge_unique_lists(pg["competitor_domains_mentioned"], dm["competitor_domains_mentioned"])),
        "competitor_anchor_examples" : " | ".join(merge_unique_lists(pg["competitor_anchor_examples"],   dm["competitor_anchor_examples"])[:10]),

        "target_page_link_policy"            : pg.get("page_link_policy", "unknown"),
        "domain_link_policy"                 : dm.get("page_link_policy", "unknown"),
        "target_page_external_follow_types"  : " | ".join(pg.get("page_external_follow_types", [])) or "none",
        "domain_external_follow_types"       : " | ".join(dm.get("page_external_follow_types", [])) or "none",
        "target_page_extracted_keywords"     : " | ".join(pg["extracted_keywords"]),
        "target_page_anchor_text_suggestions": " | ".join(pg["anchor_text_suggestions"]),
        "domain_anchor_text_suggestions"     : " | ".join(dm["anchor_text_suggestions"]),

        "priority_score": choose_final_score(pg, dm),
        "priority_label": choose_final_label(pg, dm),
        "action"        : choose_final_action(pg, dm),
        "notes"         : notes,
        "error"         : " | ".join(filter(None, [pg["error"], dm["error"]])),
    }


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    qualified = df[df["action"] == "qualified"].copy()
    review    = df[df["action"] == "needs_review"].copy()
    rejected  = df[df["action"] == "reject"].copy()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer,        sheet_name="AllTargets",  index=False)
        qualified.to_excel(writer, sheet_name="Qualified",   index=False)
        review.to_excel(writer,    sheet_name="NeedsReview", index=False)
        rejected.to_excel(writer,  sheet_name="Rejected",    index=False)
    return out.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="main-header">🔗 BL Tool</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Backlink Pipeline</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**⚙️ Configuration**")
    brand_name = st.text_input("Brand Name",     value="Jacket Cult")
    niche      = st.text_input("Niche",          value="ecommerce fashion jackets")
    money_site = st.text_input("Money Site URL", value="https://jacketcult.shop/")

    st.markdown("**Allowed Backlink Types**")
    all_types = ["guest_post","profile","social_bookmarking","web_directory",
                 "article","business_listing","email_submission","directory_business"]
    allowed_types = st.multiselect("types", options=all_types, default=all_types,
                                   label_visibility="collapsed")

    st.divider()
    st.markdown("**🔧 Request Settings**")
    timeout    = st.number_input("Timeout (seconds)", min_value=5, max_value=60, value=20)
    user_agent = st.text_input("User Agent",
                               value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    st.divider()
    st.markdown("**📊 Priority Thresholds**")
    high_thresh   = st.slider("High",   50, 100, 75)
    medium_thresh = st.slider("Medium", 20,  74, 50)

    st.divider()
    st.caption("v1.0 · Backlink Intelligence Tool")

config = {
    "brand_name": brand_name, "niche": niche,
    "allowed_backlink_types": allowed_types,
    "priority_thresholds": {"high": high_thresh, "medium": medium_thresh},
    "request": {"timeout_seconds": timeout, "user_agent": user_agent},
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="main-header">Backlink Intelligence Pipeline</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload → Configure → Analyze → Export</div>', unsafe_allow_html=True)

# ── Show import error with full traceback if modules failed to load ───────────
if _IMPORT_ERROR:
    st.error("❌ Could not load pipeline modules. Full error below:")
    st.code(_IMPORT_ERROR, language="python")
    st.info(f"**Debug info:**\n- ROOT: `{_ROOT}`\n- sys.path[0]: `{sys.path[0]}`\n- Files in ROOT: `{os.listdir(_ROOT)}`")
    st.stop()

# ─── Upload ───────────────────────────────────────────────────────────────────
col_up, col_tpl = st.columns([3, 1])
with col_up:
    uploaded = st.file_uploader("Upload targets.csv", type=["csv"],
        help="Must have a `url` column. Optional: brand, niche, competitors, notes")
with col_tpl:
    st.markdown("<br>", unsafe_allow_html=True)
    sample = "url,brand,niche,competitors,notes\nhttps://example.com/blog,My Brand,fashion jackets,comp1.com|comp2.com,test\n"
    st.download_button("📄 Sample CSV", data=sample, file_name="targets_sample.csv",
                       mime="text/csv", use_container_width=True)

# ─── Preview ──────────────────────────────────────────────────────────────────
if uploaded:
    df_input = pd.read_csv(uploaded)
    if "url" not in df_input.columns:
        st.error("❌ CSV must have a `url` column.")
        st.stop()

    with st.expander(f"📋 Preview — {len(df_input)} rows", expanded=False):
        st.dataframe(df_input, use_container_width=True, height=200)

    st.divider()

    col_btn, col_inf = st.columns([1, 3])
    with col_btn:
        run_btn = st.button("▶  Run Pipeline", use_container_width=True)
    with col_inf:
        st.info(f"Will process **{len(df_input)} URLs** × 2 requests each (page + root domain)")

    if run_btn:
        rows_out, errors = [], []
        total    = len(df_input)
        progress = st.progress(0, text="Starting…")
        status   = st.empty()

        for i, (_, row) in enumerate(df_input.iterrows()):
            url = str(row.get("url", "")).strip()
            progress.progress(int(i / total * 100), text=f"Processing {i+1}/{total} — {url[:70]}…")
            status.markdown(f"`→ {url}`")
            try:
                rows_out.append(run_row(row, brand_name, niche, allowed_types,
                                        timeout, user_agent, config))
            except Exception as e:
                errors.append(f"Row {i+1} ({url}): {e}")
                rows_out.append({"source_url": url, "error": str(e),
                                 "action": "needs_review", "priority_score": 0, "priority_label": "low"})

        progress.progress(100, text="✅ Done!")
        status.empty()
        st.session_state["results_df"]      = pd.DataFrame(rows_out)
        st.session_state["pipeline_errors"] = errors

# ─── Results ──────────────────────────────────────────────────────────────────
if "results_df" in st.session_state:
    df = st.session_state["results_df"]
    st.divider()

    total     = len(df)
    qualified = int((df["action"] == "qualified").sum())    if "action"         in df.columns else 0
    review    = int((df["action"] == "needs_review").sum()) if "action"         in df.columns else 0
    rejected  = int((df["action"] == "reject").sum())       if "action"         in df.columns else 0
    avg_score = int(df["priority_score"].mean())             if "priority_score" in df.columns and total else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    for col, val, lbl in [(c1,total,"TOTAL"),(c2,qualified,"QUALIFIED"),
                          (c3,review,"NEEDS REVIEW"),(c4,rejected,"REJECTED"),(c5,avg_score,"AVG SCORE")]:
        col.markdown(f'<div class="metric-card"><div class="value">{val}</div><div class="label">{lbl}</div></div>',
                     unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get("pipeline_errors"):
        with st.expander(f"⚠️ {len(st.session_state['pipeline_errors'])} errors"):
            for e in st.session_state["pipeline_errors"]:
                st.code(e)

    show_cols = [c for c in [
        "source_url","target_page_backlink_type","target_page_niche_relevant",
        "target_page_allowed_type","priority_score","priority_label","action",
        "target_page_status_code","target_page_indexable","competitor_linked",
        "target_page_link_policy","target_page_anchor_text_suggestions","notes","error",
    ] if c in df.columns]

    def score_color(val):
        try:
            v = int(val)
            if v >= 75: return "color:#5dde5d"
            if v >= 50: return "color:#f0b429"
            return "color:#e05555"
        except: return ""

    tab_all,tab_q,tab_r,tab_rej,tab_exp = st.tabs([
        "📊 All","✅ Qualified","🔍 Needs Review","❌ Rejected","💾 Export"])

    def show_df(subset):
        if subset.empty:
            st.info("No results in this category.")
            return
        cols = [c for c in show_cols if c in subset.columns]
        st.dataframe(
            subset[cols].style.applymap(score_color,
                subset=["priority_score"] if "priority_score" in cols else []),
            use_container_width=True, height=480)

    with tab_all: show_df(df)
    with tab_q:
        st.markdown(f"**{qualified} qualified prospects**")
        show_df(df[df["action"]=="qualified"] if "action" in df.columns else df)
    with tab_r:
        st.markdown(f"**{review} URLs need manual review**")
        show_df(df[df["action"]=="needs_review"] if "action" in df.columns else df)
    with tab_rej:
        st.markdown(f"**{rejected} URLs rejected**")
        show_df(df[df["action"]=="reject"] if "action" in df.columns else df)

    with tab_exp:
        st.markdown("### Export Results")
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        col_xl, col_cs = st.columns(2)
        with col_xl:
            st.markdown("**Excel (.xlsx) — 4 sheets**")
            st.caption("AllTargets · Qualified · NeedsReview · Rejected")
            st.download_button("⬇️ Download Excel", data=to_excel_bytes(df),
                               file_name=f"backlink_pipeline_{ts}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        with col_cs:
            st.markdown("**CSV (.csv)**")
            st.caption("Flat file for further processing")
            st.download_button("⬇️ Download CSV",
                               data=df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
                               file_name=f"backlink_pipeline_{ts}.csv",
                               mime="text/csv", use_container_width=True)
        st.divider()
        st.dataframe(df, use_container_width=True, height=400)

else:
    st.markdown("""
    <div style="text-align:center;padding:5rem 2rem;color:#444;">
        <div style="font-size:4rem;margin-bottom:1rem;">🔗</div>
        <div style="font-family:'Space Mono',monospace;font-size:1.1rem;color:#666;margin-bottom:0.5rem;">
            Upload a CSV to get started
        </div>
        <div style="font-size:0.82rem;color:#444;letter-spacing:1px;text-transform:uppercase;">
            CSV must contain a <code style="color:#c8f135">url</code> column
        </div>
    </div>
    """, unsafe_allow_html=True)
PYEOF
echo "Done — $(wc -l < /home/claude/backlink-tool/streamlit_app.py) lines"
