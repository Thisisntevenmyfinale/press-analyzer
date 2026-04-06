import streamlit as st

from src.article_extractor import extract_article_from_url
from src.claim_analyzer import (
    get_client,
    extract_claims,
    analyze_claim,
    analyze_missing_perspectives,
    editorial_decision,
    rewrite_neutral,
    stakeholder_review,
    press_scorecard,
)
from src.indicators import compute_indicators
from src.scoring import (
    indicator_based_scores,
    merge_scores,
    decision_hint_from_scores,
    classify_claim_type,
    claim_risk_score,
    headline_body_consistency,
    final_editorial_verdict,
)
from src.utils import average_score, risk_badge_label

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PressAnalyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Demo article
# ─────────────────────────────────────────────────────────────────────────────
DEMO_ARTICLE = """
Die Gier ist zurück an der Wall Street, und sie trägt die Handschrift von Elon Musk und Sam Altman. Während die globale Geopolitik durch den Konflikt im Nahen Osten in den Grundfesten erschüttert wird, bereitet sich die US-Börse auf ein Spektakel vor, das alle bisherigen Dimensionen sprengen könnte. Die Zahlen des ersten Quartals 2026 sprechen eine deutliche Sprache: Das Emissionsvolumen bei Aktienverkäufen schoss um 40 Prozent auf atemberaubende 211 Milliarden Dollar nach oben. Es ist der stärkste Jahresauftakt seit dem Rekordjahr 2021 – ein finanzielles Hochamt inmitten des globalen Chaos.

Doch die eigentliche Prüfung steht erst noch bevor. Der Markt bereitet sich auf den „Urknall" vor: SpaceX steht kurz davor, an die Börse zu gehen. Mit einer angestrebten Bewertung von bis zu 1,75 Billionen Dollar und einem geplanten Emissionsvolumen von über 75 Milliarden Dollar wäre dies nicht nur ein Börsengang, sondern eine Machtdemonstration des Silicon Valley gegenüber der klassischen Industrie.

Hinter dem Weltraum-Giganten SpaceX drängt die nächste Welle der Disruption auf das Parkett. OpenAI und der Konkurrent Anthropic prüfen laut Insidern Listings, die ebenfalls zweistellige Milliardenbeträge in die Kassen spülen sollen. Diese KI-Infrastruktur-Titel erweisen sich als erstaunlich resistent gegenüber der allgemeinen Software-Schwäche.

„Die Widerstandsfähigkeit, die wir in diesem Markt angesichts all der Turbulenzen da draußen gesehen haben, ist ganz bemerkenswert", so John Kolz, Global Head of Equity Capital Markets bei Barclays.

Während in den USA die Tech-Träume die Kurse treiben, zeigt sich in Europa ein deutlich nüchterneres, aber ebenso lukratives Bild. Hier ist das IPO-Geschäft fest in der Hand der Rüstungsindustrie. Der tschechische Verteidigungskonzern CSG markierte mit einem 4,5-Milliarden-Dollar-Börsengang das bisherige Highlight des Quartals.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

:root {
  --bg:        #0a0a0f;
  --surface:   #111118;
  --surface2:  #16161f;
  --border:    rgba(255,255,255,0.08);
  --border2:   rgba(255,255,255,0.14);
  --text:      #e8e6f0;
  --muted:     #888899;
  --accent:    #7c6af7;
  --accent2:   #a89cf8;
  --red:       #f04060;
  --amber:     #f0a030;
  --green:     #30c080;
  --mono:      'IBM Plex Mono', monospace;
  --sans:      'IBM Plex Sans', sans-serif;
}

html, body, .stApp { background: var(--bg) !important; font-family: var(--sans); }

.main .block-container {
  max-width: 1280px;
  padding: 1.5rem 2rem 4rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border2) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stTextInput label { font-size: 0.82rem !important; }

/* Global text */
h1,h2,h3,h4,h5,p,li,div,span,label { color: var(--text); }
.stMarkdown p { color: var(--text); line-height: 1.7; }

/* Inputs */
.stTextInput input, .stTextArea textarea {
  background: var(--surface2) !important;
  border: 1px solid var(--border2) !important;
  color: var(--text) !important;
  font-family: var(--sans) !important;
  border-radius: 0 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(124,106,247,0.2) !important;
}

/* Buttons */
.stButton > button {
  background: var(--accent) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 0 !important;
  font-family: var(--mono) !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  padding: 0.6rem 1.4rem !important;
  transition: background 0.15s;
}
.stButton > button:hover { background: #9080ff !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-bottom: 1px solid var(--border2) !important;
  gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: var(--mono) !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  border-radius: 0 !important;
  padding: 0.6rem 1.2rem !important;
  border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent2) !important;
  border-bottom-color: var(--accent) !important;
  background: var(--surface2) !important;
}

/* Expander */
.stExpander { border: 1px solid var(--border) !important; background: var(--surface) !important; border-radius: 0 !important; }
.stExpander summary { font-family: var(--mono) !important; font-size: 0.82rem !important; color: var(--text) !important; }

/* Status / spinner */
.stStatus { background: var(--surface) !important; border: 1px solid var(--border2) !important; }

/* Metric */
[data-testid="stMetric"] { background: var(--surface) !important; padding: 1rem !important; border: 1px solid var(--border) !important; }
[data-testid="stMetricValue"] { font-family: var(--mono) !important; color: #fff !important; font-size: 1.6rem !important; }
[data-testid="stMetricLabel"] { font-family: var(--mono) !important; font-size: 0.72rem !important; color: var(--muted) !important; text-transform: uppercase; letter-spacing: 0.1em; }

/* Alert */
.stAlert { border-radius: 0 !important; }

/* JSON */
.stJson { background: var(--surface2) !important; border: 1px solid var(--border) !important; }

/* Code */
.stCode, .stCodeBlock { background: var(--surface2) !important; font-family: var(--mono) !important; }

/* Custom components */
.pa-header {
  border-bottom: 1px solid var(--border2);
  padding-bottom: 1.4rem;
  margin-bottom: 1.8rem;
}
.pa-wordmark {
  font-family: var(--mono);
  font-size: 1.6rem;
  font-weight: 600;
  color: #fff;
  letter-spacing: -0.02em;
}
.pa-wordmark span { color: var(--accent); }
.pa-tagline {
  font-size: 0.85rem;
  color: var(--muted);
  margin-top: 0.3rem;
}

.pa-verdict {
  border: 1px solid var(--border2);
  background: var(--surface);
  padding: 1.6rem 1.8rem;
  margin-bottom: 1.4rem;
  position: relative;
  overflow: hidden;
}
.pa-verdict::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 4px; height: 100%;
}
.pa-verdict.publish::before  { background: var(--green); }
.pa-verdict.revise::before   { background: var(--amber); }
.pa-verdict.review::before   { background: var(--red); }

.pa-verdict-label {
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.5rem;
}
.pa-verdict-title {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  color: #fff;
  margin-bottom: 0.6rem;
}
.pa-verdict.publish  .pa-verdict-title { color: var(--green); }
.pa-verdict.revise   .pa-verdict-title { color: var(--amber); }
.pa-verdict.review   .pa-verdict-title { color: var(--red); }
.pa-verdict-hint {
  font-size: 0.92rem;
  color: var(--muted);
  line-height: 1.6;
  max-width: 700px;
}

.pa-meta-row {
  display: flex;
  gap: 1rem;
  margin-top: 1.2rem;
  flex-wrap: wrap;
}
.pa-meta-chip {
  border: 1px solid var(--border2);
  background: var(--surface2);
  padding: 0.45rem 0.85rem;
  font-family: var(--mono);
  font-size: 0.75rem;
}
.pa-meta-chip .chip-key { color: var(--muted); margin-right: 0.4rem; }
.pa-meta-chip .chip-val { color: #fff; font-weight: 600; }

.pa-panel {
  border: 1px solid var(--border);
  background: var(--surface);
  padding: 1.2rem 1.4rem;
  height: 100%;
}
.pa-panel-title {
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent2);
  margin-bottom: 0.9rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--border);
}
.pa-panel ul { padding-left: 1.1rem; margin: 0; }
.pa-panel li { color: var(--text); font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.5rem; }
.pa-panel p  { color: var(--text); font-size: 0.9rem; line-height: 1.6; margin: 0; }

.pa-score-row {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.9rem;
}
.pa-score-label {
  font-family: var(--mono);
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--muted);
  width: 120px;
  flex-shrink: 0;
}
.pa-score-bar-bg {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--border);
  overflow: hidden;
}
.pa-score-bar-fill { height: 100%; transition: width 0.4s ease; }
.pa-score-num {
  font-family: var(--mono);
  font-size: 0.78rem;
  font-weight: 600;
  color: #fff;
  width: 34px;
  text-align: right;
  flex-shrink: 0;
}

.pa-claim-card {
  border: 1px solid var(--border);
  background: var(--surface);
  padding: 1rem 1.1rem;
  margin-bottom: 0.8rem;
  position: relative;
  padding-left: 1.6rem;
}
.pa-claim-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0;
  width: 3px; height: 100%;
}
.pa-claim-card.high::before   { background: var(--red); }
.pa-claim-card.medium::before { background: var(--amber); }
.pa-claim-card.low::before    { background: var(--green); }

.pa-claim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.pa-claim-type {
  font-family: var(--mono);
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}
.pa-claim-badge {
  font-family: var(--mono);
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.pa-claim-badge.high   { background: rgba(240,64,96,0.15);  color: var(--red);   border: 1px solid rgba(240,64,96,0.3); }
.pa-claim-badge.medium { background: rgba(240,160,48,0.15); color: var(--amber); border: 1px solid rgba(240,160,48,0.3); }
.pa-claim-badge.low    { background: rgba(48,192,128,0.15); color: var(--green); border: 1px solid rgba(48,192,128,0.3); }

.pa-claim-text {
  font-size: 0.92rem;
  color: var(--text);
  line-height: 1.55;
  margin-bottom: 0.45rem;
}
.pa-claim-reason {
  font-size: 0.82rem;
  color: var(--muted);
  line-height: 1.5;
}

.pa-indicator-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.8rem;
  margin-bottom: 1.2rem;
}
.pa-indicator-box {
  border: 1px solid var(--border);
  background: var(--surface);
  padding: 0.85rem 1rem;
  text-align: center;
}
.pa-indicator-val {
  font-family: var(--mono);
  font-size: 1.7rem;
  font-weight: 700;
  color: #fff;
  line-height: 1;
}
.pa-indicator-key {
  font-family: var(--mono);
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
  margin-top: 0.3rem;
}

.pa-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1.4rem 0;
}

.pa-section-label {
  font-family: var(--mono);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.8rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border);
}

.pa-consistency-badge {
  display: inline-block;
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.pa-consistency-badge.strong   { background: rgba(48,192,128,0.15); color: var(--green); border: 1px solid rgba(48,192,128,0.3); }
.pa-consistency-badge.moderate { background: rgba(240,160,48,0.15); color: var(--amber); border: 1px solid rgba(240,160,48,0.3); }
.pa-consistency-badge.weak     { background: rgba(240,64,96,0.15);  color: var(--red);   border: 1px solid rgba(240,64,96,0.3); }

@media (max-width: 900px) {
  .pa-indicator-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def ensure_state():
    defaults = {
        "article_text": "",
        "article_url": "",
        "use_demo": False,
        "analysis_complete": False,
        "analysis_running": False,
        "analysis": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_api_key():
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None


def safe_preview(text: str, limit: int = 200) -> str:
    text = " ".join(text.split())
    return text[:limit].rstrip() + "…" if len(text) > limit else text


def risk_css_class(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 55:
        return "medium"
    return "low"


def risk_label(score: int) -> str:
    if score >= 75:
        return "High risk"
    if score >= 55:
        return "Med risk"
    return "Low risk"


def score_color(score: int) -> str:
    if score >= 75:
        return "#30c080"
    if score >= 55:
        return "#f0a030"
    return "#f04060"


def verdict_css_class(status: str) -> str:
    if status == "Publish":
        return "publish"
    if status == "Revise":
        return "revise"
    return "review"


def verdict_display(status: str) -> str:
    if status == "Publish":
        return "✓ READY TO PUBLISH"
    if status == "Revise":
        return "⚠ REVISION REQUIRED"
    return "⊗ ESCALATE FOR REVIEW"


def compact_reason(claim: str, claim_type: str, score: int) -> str:
    if claim_type in ["Predictive", "Interpretive", "Causal"]:
        return "Contains forward-looking or interpretive logic — needs stronger qualification."
    if claim_type == "Attributed allegation":
        return "Attribution quality is the primary risk factor here."
    if score >= 75:
        return "High-impact claim — requires solid evidential support before publication."
    if score >= 55:
        return "Material enough to warrant a closer sourcing review."
    return "Comparatively lower risk among extracted claims."


def top_risk_claims(claims, article_text, indicators, top_n=6):
    rows = []
    for i, claim in enumerate(claims, 1):
        score = claim_risk_score(claim, article_text, indicators)
        rows.append({
            "index": i, "claim": claim, "score": score,
            "type": classify_claim_type(claim), "label": risk_label(score),
            "css": risk_css_class(score),
        })
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[:top_n]


def run_full_analysis(client, article_text: str):
    indicators = compute_indicators(article_text)
    indicator_scores = indicator_based_scores(indicators)
    raw_scorecard, llm_scores = press_scorecard(client, article_text)
    final_scores = merge_scores(llm_scores, indicator_scores, llm_weight=0.7)
    avg = average_score(final_scores)
    quality_label = risk_badge_label(avg)
    score_hint = decision_hint_from_scores(final_scores)
    claims = extract_claims(client, article_text)
    decision_text = editorial_decision(client, article_text)
    missing_text = analyze_missing_perspectives(client, article_text)
    stakeholder_text = stakeholder_review(client, article_text)
    verdict = final_editorial_verdict(final_scores, indicators, claims, article_text)
    headline_label, headline_reason = headline_body_consistency(article_text)
    return {
        "indicators": indicators,
        "indicator_scores": indicator_scores,
        "raw_scorecard": raw_scorecard,
        "llm_scores": llm_scores,
        "final_scores": final_scores,
        "avg_score": avg,
        "quality_label": quality_label,
        "score_hint": score_hint,
        "claims": claims,
        "decision_text": decision_text,
        "missing_text": missing_text,
        "stakeholder_text": stakeholder_text,
        "verdict": verdict,
        "headline_label": headline_label,
        "headline_reason": headline_reason,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
ensure_state()

with st.sidebar:
    st.markdown("### ⚙ Configuration")
    st.divider()

    secret_key = get_api_key()
    if secret_key:
        st.success("OpenAI key loaded from secrets", icon="🔑")
        api_key = secret_key
    else:
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")

    st.divider()
    input_mode = st.radio("Input mode", ["Paste article text", "Article URL"], index=1)
    review_mode = st.radio("Workspace mode", ["Editor (compact)", "Analyst (full)"], index=0)

    st.divider()
    st.markdown("**Demo**")
    if st.button("Load demo article", use_container_width=True):
        st.session_state.update({
            "article_text": DEMO_ARTICLE,
            "use_demo": True,
            "analysis_complete": False,
            "analysis_running": False,
            "analysis": None,
        })
        st.rerun()

    st.divider()
    st.markdown(
        "<span style='font-size:0.76rem;color:#666;font-family:IBM Plex Mono,monospace'>"
        "PressAnalyzer · Pre-publication review prototype"
        "</span>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pa-header">
  <div class="pa-wordmark">Press<span>Analyzer</span></div>
  <div class="pa-tagline">Pre-publication editorial review · claim risk triage · sourcing & balance audit</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Input section
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="pa-section-label">Input</div>', unsafe_allow_html=True)

col_input, col_info = st.columns([2.4, 1], gap="large")

with col_input:
    if input_mode == "Paste article text":
        article_text_input = st.text_area(
            "Article text",
            value=st.session_state.get("article_text", ""),
            height=280,
            placeholder="Paste a full article draft here...",
            label_visibility="collapsed",
        )
        st.session_state["article_text"] = article_text_input
    else:
        article_url = st.text_input(
            "Article URL",
            value=st.session_state.get("article_url", ""),
            placeholder="https://www.reuters.com/...",
            label_visibility="collapsed",
        )
        st.session_state["article_url"] = article_url
        if article_url.strip():
            try:
                extracted = extract_article_from_url(article_url.strip())
                st.session_state["article_text"] = extracted
                st.success(f"Extracted {len(extracted.split())} words.")
                with st.expander("Preview extracted text"):
                    st.write(extracted[:3000])
            except Exception as e:
                st.error(f"Extraction failed: {e}")

    run_btn = st.button("▶  Run Editorial Audit", use_container_width=True)

with col_info:
    st.markdown("""
<div class="pa-panel">
  <div class="pa-panel-title">What this tool checks</div>
  <ul>
    <li><strong>Sourcing</strong> — named attribution density</li>
    <li><strong>Balance</strong> — stakeholder coverage</li>
    <li><strong>Tone Neutrality</strong> — loaded language</li>
    <li><strong>Transparency</strong> — fact vs. inference</li>
    <li><strong>Claim Risk</strong> — per-claim triage</li>
    <li><strong>Missing Voices</strong> — gaps analysis</li>
  </ul>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Run analysis
# ─────────────────────────────────────────────────────────────────────────────
article_text = st.session_state.get("article_text", "")

if run_btn:
    if not api_key:
        st.warning("Please enter an OpenAI API key.")
        st.stop()
    if len(article_text.strip()) < 250:
        st.warning("Article is too short. Please provide at least a few paragraphs.")
        st.stop()

    st.session_state.update({"analysis_running": True, "analysis_complete": False, "analysis": None})

    with st.status("Running editorial analysis…", expanded=True) as status_box:
        st.write("🔍 Computing structural indicators…")
        st.write("📊 Scoring sourcing, transparency, balance and tone…")
        st.write("🧩 Extracting high-impact claims…")
        st.write("🗣 Running missing-perspective and panel review…")
        result = run_full_analysis(get_client(api_key), article_text)
        status_box.update(label="Analysis complete ✓", state="complete")

    st.session_state.update({"analysis": result, "analysis_running": False, "analysis_complete": True})


# ─────────────────────────────────────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.get("analysis_complete") and st.session_state.get("analysis"):
    d = st.session_state["analysis"]

    indicators    = d["indicators"]
    final_scores  = d["final_scores"]
    avg_score     = d["avg_score"]
    quality_label = d["quality_label"]
    score_hint    = d["score_hint"]
    claims        = d["claims"]
    decision_text = d["decision_text"]
    missing_text  = d["missing_text"]
    stakeholder_text = d["stakeholder_text"]
    verdict       = d["verdict"]
    headline_label = d["headline_label"]
    headline_reason = d["headline_reason"]
    raw_scorecard = d["raw_scorecard"]
    indicator_scores = d["indicator_scores"]

    top_claims = top_risk_claims(claims, article_text, indicators, top_n=6)

    st.markdown('<hr class="pa-divider">', unsafe_allow_html=True)

    # ── Verdict ──────────────────────────────────────────────────────────────
    st.markdown('<div class="pa-section-label">Editorial Verdict</div>', unsafe_allow_html=True)

    css_class = verdict_css_class(verdict["status"])
    hl = headline_label.lower()
    if hl not in ("strong", "moderate", "weak"):
        hl = "moderate"

    st.markdown(f"""
<div class="pa-verdict {css_class}">
  <div class="pa-verdict-label">Final editorial decision</div>
  <div class="pa-verdict-title">{verdict_display(verdict['status'])}</div>
  <div class="pa-verdict-hint">{score_hint}</div>
  <div class="pa-meta-row">
    <div class="pa-meta-chip"><span class="chip-key">Severity</span><span class="chip-val">{verdict['severity']}</span></div>
    <div class="pa-meta-chip"><span class="chip-key">Confidence</span><span class="chip-val">{verdict['confidence']}</span></div>
    <div class="pa-meta-chip"><span class="chip-key">Quality</span><span class="chip-val">{quality_label}</span></div>
    <div class="pa-meta-chip"><span class="chip-key">Avg score</span><span class="chip-val">{avg_score if avg_score else 'N/A'}</span></div>
    <div class="pa-meta-chip"><span class="chip-key">Headline/body</span><span class="chip-val">{headline_label}</span></div>
    <div class="pa-meta-chip"><span class="chip-key">Claims found</span><span class="chip-val">{len(claims)}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── 3-column focus panels ─────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        items = verdict["blocking_issues"] or ["No blocking issues automatically detected."]
        li_html = "".join(f"<li>{i}</li>" for i in items)
        st.markdown(f"""
<div class="pa-panel">
  <div class="pa-panel-title">🚫 Blocking issues</div>
  <ul>{li_html}</ul>
</div>""", unsafe_allow_html=True)

    with c2:
        items = verdict["required_actions"] or ["No mandatory actions detected."]
        li_html = "".join(f"<li>{i}</li>" for i in items)
        st.markdown(f"""
<div class="pa-panel">
  <div class="pa-panel-title">🔧 Required actions</div>
  <ul>{li_html}</ul>
</div>""", unsafe_allow_html=True)

    with c3:
        items = verdict["non_blocking_issues"] or ["No non-blocking issues detected."]
        li_html = "".join(f"<li>{i}</li>" for i in items)
        st.markdown(f"""
<div class="pa-panel">
  <div class="pa-panel-title">ℹ Non-blocking notes</div>
  <ul>{li_html}</ul>
</div>""", unsafe_allow_html=True)

    st.markdown('<hr class="pa-divider">', unsafe_allow_html=True)

    # ── Scores + Indicators row ───────────────────────────────────────────────
    st.markdown('<div class="pa-section-label">Quality Scores &amp; Structural Indicators</div>', unsafe_allow_html=True)

    sc_col, ind_col = st.columns([1, 1.4], gap="large")

    with sc_col:
        st.markdown('<div class="pa-panel">', unsafe_allow_html=True)
        st.markdown('<div class="pa-panel-title">Merged scores (LLM 70% + indicators 30%)</div>', unsafe_allow_html=True)
        for label in ["Balance", "Sourcing", "Tone Neutrality", "Transparency"]:
            score = final_scores.get(label)
            if score is None:
                st.write(f"**{label}:** N/A")
                continue
            color = score_color(score)
            st.markdown(f"""
<div class="pa-score-row">
  <div class="pa-score-label">{label}</div>
  <div class="pa-score-bar-bg">
    <div class="pa-score-bar-fill" style="width:{score}%;background:{color};"></div>
  </div>
  <div class="pa-score-num">{score}</div>
</div>""", unsafe_allow_html=True)

        # Headline/body consistency
        hl_badge_class = headline_label.lower() if headline_label.lower() in ("strong","moderate","weak") else "moderate"
        st.markdown(f"""
<div style="margin-top:1rem;border-top:1px solid var(--border);padding-top:0.9rem;">
  <div style="font-family:var(--mono);font-size:0.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Headline / Body consistency</div>
  <span class="pa-consistency-badge {hl_badge_class}">{headline_label}</span>
  <div style="font-size:0.82rem;color:var(--muted);margin-top:0.5rem;line-height:1.5">{headline_reason}</div>
</div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ind_col:
        st.markdown('<div class="pa-panel">', unsafe_allow_html=True)
        st.markdown('<div class="pa-panel-title">Deterministic text indicators</div>', unsafe_allow_html=True)

        ind_items = [
            ("quotes", "Quotes"),
            ("attributions", "Attributions"),
            ("numbers", "Numbers"),
            ("loaded_words", "Loaded words"),
            ("hedges", "Hedges"),
            ("named_sources", "Named sources"),
            ("stakeholder_hints", "Stakeholder hints"),
        ]
        rows_html = ""
        for key, label in ind_items:
            val = indicators.get(key, 0)
            # flag concern vs ok
            concern = False
            if key == "named_sources" and val < 2:
                concern = True
            if key == "attributions" and val < 2:
                concern = True
            if key == "loaded_words" and val >= 3:
                concern = True
            color = "var(--red)" if concern else "var(--text)"
            rows_html += f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:0.35rem 0;border-bottom:1px solid var(--border);">
  <span style="font-size:0.85rem;color:var(--muted)">{label}</span>
  <span style="font-family:var(--mono);font-size:0.95rem;font-weight:700;color:{color}">{val}</span>
</div>"""
        st.markdown(rows_html, unsafe_allow_html=True)
        st.markdown("""
<div style="font-size:0.75rem;color:var(--muted);margin-top:0.7rem;line-height:1.5">
  Red values indicate indicators outside recommended thresholds.
</div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="pa-divider">', unsafe_allow_html=True)

    # ── Claim risk map ────────────────────────────────────────────────────────
    st.markdown('<div class="pa-section-label">Claim Risk Map</div>', unsafe_allow_html=True)

    if not top_claims:
        st.info("No claims were extracted from this article.")
    else:
        left_claims = top_claims[:3]
        right_claims = top_claims[3:]

        clm_left, clm_right = st.columns(2, gap="large")

        for col, batch in [(clm_left, left_claims), (clm_right, right_claims)]:
            with col:
                for row in batch:
                    reason = compact_reason(row["claim"], row["type"], row["score"])
                    st.markdown(f"""
<div class="pa-claim-card {row['css']}">
  <div class="pa-claim-header">
    <span class="pa-claim-type">#{row['index']} · {row['type']}</span>
    <span class="pa-claim-badge {row['css']}">{row['label']} · {row['score']}/100</span>
  </div>
  <div class="pa-claim-text">{safe_preview(row['claim'], 220)}</div>
  <div class="pa-claim-reason">{reason}</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<hr class="pa-divider">', unsafe_allow_html=True)

    # ── Deep analysis tabs ────────────────────────────────────────────────────
    st.markdown('<div class="pa-section-label">Deep Analysis</div>', unsafe_allow_html=True)

    if "Editor" in review_mode:
        tabs = st.tabs(["Missing Perspectives", "Editorial Panel", "Claim Review", "Revision", "Raw / Debug"])
    else:
        tabs = st.tabs(["Decision Report", "Missing Perspectives", "Editorial Panel", "Claim Review", "Revision", "Indicators", "Raw / Debug"])

    def tab_missing(tab):
        with tab:
            st.subheader("Missing voices, evidence & context")
            st.write(missing_text)

    def tab_panel(tab):
        with tab:
            st.subheader("Simulated editorial panel")
            st.write(stakeholder_text)

    def tab_claims(tab):
        with tab:
            st.subheader("Claim-by-claim deep review")
            if not claims:
                st.info("No claims extracted.")
                return
            for i, claim in enumerate(claims, 1):
                ctype = classify_claim_type(claim)
                risk = claim_risk_score(claim, article_text, indicators)
                with st.expander(f"Claim {i}  ·  {ctype}  ·  {risk}/100"):
                    st.markdown(f"**Claim:** {claim}")
                    with st.spinner("Analysing claim…"):
                        result = analyze_claim(get_client(api_key), claim, article_text)
                    st.write(result)

    def tab_revision(tab):
        with tab:
            st.subheader("Revision support")
            st.markdown("**Priority actions**")
            for item in (verdict["required_actions"] or ["None."]):
                st.markdown(f"- {item}")
            st.divider()
            if st.button("Generate neutral rewrite"):
                with st.spinner("Generating rewrite…"):
                    rewritten = rewrite_neutral(get_client(api_key), article_text)
                st.write(rewritten)
            else:
                st.info("Click to generate a more neutral, publication-safe rewrite of the article.")

    def tab_raw(tab):
        with tab:
            st.subheader("Raw outputs & debug data")
            st.markdown("**Senior-editor decision (LLM raw)**")
            st.write(decision_text)
            st.divider()
            st.markdown("**Raw scorecard**")
            st.code(raw_scorecard)
            st.divider()
            st.markdown("**Indicator scores (deterministic)**")
            st.json(indicator_scores)
            st.markdown("**Final merged scores**")
            st.json(final_scores)

    if "Editor" in review_mode:
        tab_missing(tabs[0])
        tab_panel(tabs[1])
        tab_claims(tabs[2])
        tab_revision(tabs[3])
        tab_raw(tabs[4])
    else:
        with tabs[0]:
            st.subheader("Pre-publication decision report")
            st.markdown(f"**Status:** `{verdict['status']}`  |  **Severity:** `{verdict['severity']}`  |  **Confidence:** `{verdict['confidence']}`")
            st.divider()
            st.markdown("**Blocking issues**")
            for item in (verdict["blocking_issues"] or ["None."]):
                st.markdown(f"- {item}")
            st.markdown("**Non-blocking issues**")
            for item in (verdict["non_blocking_issues"] or ["None."]):
                st.markdown(f"- {item}")
            st.markdown("**Required actions**")
            for item in (verdict["required_actions"] or ["None."]):
                st.markdown(f"- {item}")
            st.divider()
            st.markdown("**LLM senior-editor decision**")
            st.write(decision_text)

        tab_missing(tabs[1])
        tab_panel(tabs[2])
        tab_claims(tabs[3])
        tab_revision(tabs[4])

        with tabs[5]:
            st.subheader("Indicators & scoring detail")
            st.markdown("**Raw indicators**")
            st.json(indicators)
            st.markdown("**Indicator-derived scores**")
            st.json(indicator_scores)
            st.markdown("**LLM scores**")
            st.json(d["llm_scores"])
            st.markdown("**Final merged scores**")
            st.json(final_scores)

        tab_raw(tabs[6])

elif st.session_state.get("analysis_running"):
    st.info("Analysis is running…")