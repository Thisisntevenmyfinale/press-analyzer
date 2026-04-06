import streamlit as st
from datetime import date

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
st.set_page_config(
    page_title="PressAnalyzer",
    page_icon="🗞",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEMO_ARTICLE = """Die Gier ist zurück an der Wall Street, und sie trägt die Handschrift von Elon Musk und Sam Altman. Während die globale Geopolitik durch den Konflikt im Nahen Osten in den Grundfesten erschüttert wird, bereitet sich die US-Börse auf ein Spektakel vor, das alle bisherigen Dimensionen sprengen könnte. Die Zahlen des ersten Quartals 2026 sprechen eine deutliche Sprache: Das Emissionsvolumen bei Aktienverkäufen schoss um 40 Prozent auf atemberaubende 211 Milliarden Dollar nach oben. Es ist der stärkste Jahresauftakt seit dem Rekordjahr 2021 – ein finanzielles Hochamt inmitten des globalen Chaos.

Doch die eigentliche Prüfung steht erst noch bevor. Der Markt bereitet sich auf den „Urknall" vor: SpaceX steht kurz davor, an die Börse zu gehen. Mit einer angestrebten Bewertung von bis zu 1,75 Billionen Dollar und einem geplanten Emissionsvolumen von über 75 Milliarden Dollar wäre dies nicht nur ein Börsengang, sondern eine Machtdemonstration des Silicon Valley gegenüber der klassischen Industrie.

Hinter dem Weltraum-Giganten SpaceX drängt die nächste Welle der Disruption auf das Parkett. OpenAI und der Konkurrent Anthropic prüfen laut Insidern Listings, die ebenfalls zweistellige Milliardenbeträge in die Kassen spülen sollen. Diese KI-Infrastruktur-Titel erweisen sich als erstaunlich resistent gegenüber der allgemeinen Software-Schwäche.

„Die Widerstandsfähigkeit, die wir in diesem Markt angesichts all der Turbulenzen da draußen gesehen haben, ist ganz bemerkenswert", so John Kolz, Global Head of Equity Capital Markets bei Barclays.

Während in den USA die Tech-Träume die Kurse treiben, zeigt sich in Europa ein deutlich nüchterneres, aber ebenso lukratives Bild. Hier ist das IPO-Geschäft fest in der Hand der Rüstungsindustrie. Der tschechische Verteidigungskonzern CSG markierte mit einem 4,5-Milliarden-Dollar-Börsengang das bisherige Highlight des Quartals.""".strip()

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,600;1,8..60,300;1,8..60,400&family=DM+Mono:wght@400;500&display=swap');

:root {
  --ink:        #0d0d0d;
  --paper:      #f5f0e8;
  --paper2:     #ede8dc;
  --paper3:     #fff;
  --rule:       #1a1a1a;
  --rule-light: #c8bfaa;
  --red:        #c0161e;
  --red-bg:     #fef2f2;
  --amber:      #b56a00;
  --amber-bg:   #fef8ec;
  --green:      #1a6b3c;
  --green-bg:   #f0faf5;
  --muted:      #5a5245;
  --serif:      'Playfair Display', Georgia, serif;
  --body:       'Source Serif 4', Georgia, serif;
  --mono:       'DM Mono', 'Courier New', monospace;
}

html, body, .stApp { background: var(--paper) !important; }
.main .block-container { max-width: 1320px; padding: 0 2rem 5rem; background: var(--paper); }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: var(--ink) !important; border-right: none !important; }
[data-testid="stSidebar"] * { color: #d8d0c4 !important; font-family: var(--mono) !important; font-size: 0.78rem !important; }
[data-testid="stSidebar"] .stTextInput input {
  background: #1c1c1c !important; border: 1px solid #3a3a3a !important;
  color: #e8e0d0 !important; border-radius: 0 !important;
}
[data-testid="stSidebar"] .stTextInput input:focus { border-color: var(--red) !important; box-shadow: none !important; }
[data-testid="stSidebar"] .stButton > button {
  background: var(--red) !important; color: #fff !important; border: none !important;
  border-radius: 0 !important; letter-spacing: 0.12em !important; text-transform: uppercase !important;
}
[data-testid="stSidebar"] .stButton > button:hover { background: #9a1016 !important; }
[data-testid="stSidebar"] hr { border-color: #2a2a2a !important; }
[data-testid="stSidebar"] .stSuccess { background: #161f16 !important; border-left: 2px solid #1a6b3c !important; border-radius: 0 !important; }

/* ── Main text ── */
h1,h2,h3,h4,h5 { font-family: var(--serif) !important; color: var(--ink) !important; }
p, li { color: var(--ink); font-family: var(--body); }
.stMarkdown p { color: var(--ink); line-height: 1.8; font-family: var(--body); font-size: 0.96rem; }

/* ── Main inputs ── */
.stTextInput input, .stTextArea textarea {
  background: var(--paper3) !important; border: 1px solid var(--rule-light) !important;
  border-radius: 0 !important; color: var(--ink) !important;
  font-family: var(--body) !important; font-size: 0.95rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--ink) !important; box-shadow: none !important; }

/* ── Main button ── */
.stButton > button {
  background: var(--ink) !important; color: var(--paper) !important; border: none !important;
  border-radius: 0 !important; font-family: var(--mono) !important; font-size: 0.72rem !important;
  letter-spacing: 0.16em !important; text-transform: uppercase !important; padding: 0.65rem 1.8rem !important;
}
.stButton > button:hover { background: #2a2a2a !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--paper) !important; border-bottom: 2px solid var(--ink) !important; gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important; color: var(--muted) !important;
  font-family: var(--mono) !important; font-size: 0.68rem !important; font-weight: 500 !important;
  letter-spacing: 0.12em !important; text-transform: uppercase !important; border-radius: 0 !important;
  padding: 0.55rem 1rem !important; border-bottom: 3px solid transparent !important; margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] { color: var(--ink) !important; border-bottom-color: var(--red) !important; background: var(--paper2) !important; }

/* ── Expander ── */
.stExpander { border: 1px solid var(--rule-light) !important; background: var(--paper3) !important; border-radius: 0 !important; }
.stExpander summary { font-family: var(--mono) !important; font-size: 0.76rem !important; color: var(--ink) !important; background: var(--paper2) !important; }

/* ── Status ── */
.stStatus { background: var(--paper2) !important; border: 1px solid var(--rule-light) !important; border-left: 3px solid var(--ink) !important; border-radius: 0 !important; }

/* ── Alerts ── */
.stAlert { border-radius: 0 !important; }
.stSuccess { border-left: 3px solid var(--green) !important; }
.stWarning { border-left: 3px solid var(--amber) !important; }
.stError   { border-left: 3px solid var(--red) !important; }
.stInfo    { border-left: 3px solid var(--ink) !important; }

/* ── Code/JSON ── */
.stJson, .stCodeBlock { background: var(--paper2) !important; border: 1px solid var(--rule-light) !important; }
pre, code { font-family: var(--mono) !important; font-size: 0.78rem !important; color: var(--ink) !important; }

/* ══════════════════════════════════════════
   CUSTOM COMPONENTS
══════════════════════════════════════════ */

.pa-masthead {
  border-bottom: 4px double var(--ink);
  padding: 2rem 0 1.1rem;
  text-align: center;
  margin-bottom: 0;
}
.pa-masthead-dateline {
  font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--muted); margin-bottom: 0.55rem;
}
.pa-masthead-title {
  font-family: var(--serif); font-size: 4.6rem; font-weight: 900;
  letter-spacing: -0.025em; color: var(--ink); line-height: 1; margin-bottom: 0.45rem;
}
.pa-masthead-title span { color: var(--red); }
.pa-masthead-hrule { border: none; border-top: 1px solid var(--rule); margin: 0.55rem 0 0.3rem; }
.pa-masthead-hrule2 { border: none; border-top: 1px solid var(--rule-light); margin: 0.25rem 0 0.65rem; }
.pa-masthead-deck {
  font-family: var(--body); font-style: italic; font-size: 1rem;
  color: var(--muted); letter-spacing: 0.005em;
}
.pa-masthead-chips {
  display: flex; justify-content: center; gap: 1.6rem;
  margin-top: 0.75rem; flex-wrap: wrap;
}
.pa-masthead-chip {
  font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--muted);
}
.pa-masthead-chip::before { content: '◆ '; color: var(--red); font-size: 0.5rem; vertical-align: middle; }

.pa-section {
  font-family: var(--mono); font-size: 0.62rem; font-weight: 500;
  letter-spacing: 0.22em; text-transform: uppercase; color: var(--muted);
  border-top: 2px solid var(--ink); border-bottom: 1px solid var(--rule-light);
  padding: 0.35rem 0; margin: 1.8rem 0 1.1rem;
}

/* Verdict splash */
.pa-verdict {
  padding: 2rem 2.2rem 1.8rem; margin-bottom: 0; position: relative;
}
.pa-verdict.publish { background: var(--green); }
.pa-verdict.revise  { background: var(--amber); }
.pa-verdict.review  { background: var(--red);   }
.pa-verdict-eyebrow {
  font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.22em;
  text-transform: uppercase; color: rgba(255,255,255,0.6); margin-bottom: 0.5rem;
}
.pa-verdict-hl {
  font-family: var(--serif); font-size: 3.2rem; font-weight: 900;
  color: #fff; line-height: 1; margin-bottom: 0; text-transform: uppercase; letter-spacing: -0.01em;
}
.pa-verdict-rule { border: none; border-top: 1px solid rgba(255,255,255,0.25); margin: 0.9rem 0; }
.pa-verdict-hint {
  font-family: var(--body); font-style: italic; font-size: 1rem;
  color: rgba(255,255,255,0.85); line-height: 1.65; max-width: 820px;
}
.pa-verdict-chips { display: flex; gap: 0.6rem; flex-wrap: wrap; margin-top: 1.1rem; }
.pa-vchip {
  background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.22);
  padding: 0.28rem 0.7rem; font-family: var(--mono); font-size: 0.68rem; color: rgba(255,255,255,0.8);
}
.pa-vchip b { color: #fff; font-weight: 500; }

/* 3-panel row */
.pa-panel-row { display: grid; grid-template-columns: repeat(3,1fr); gap: 1px; background: var(--rule-light); border: 1px solid var(--rule-light); }
.pa-panel { background: var(--paper3); padding: 1.1rem 1.2rem; }
.pa-panel-head {
  font-family: var(--mono); font-size: 0.62rem; font-weight: 500;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--red);
  border-bottom: 1px solid var(--rule-light); padding-bottom: 0.5rem; margin-bottom: 0.8rem;
}
.pa-panel ul { padding-left: 1rem; margin: 0; }
.pa-panel li { font-family: var(--body); font-size: 0.87rem; line-height: 1.6; color: var(--ink); margin-bottom: 0.45rem; }

/* Box */
.pa-box { border: 1px solid var(--rule-light); background: var(--paper3); padding: 1.2rem 1.3rem; }
.pa-box-head {
  font-family: var(--mono); font-size: 0.62rem; font-weight: 500;
  letter-spacing: 0.2em; text-transform: uppercase; color: var(--muted);
  border-bottom: 2px solid var(--ink); padding-bottom: 0.5rem; margin-bottom: 1rem;
}

/* Score table */
.pa-score-row { display: flex; align-items: center; gap: 0.8rem; padding: 0.5rem 0; border-bottom: 1px solid var(--rule-light); }
.pa-score-row:last-child { border-bottom: none; }
.pa-score-lbl { font-family: var(--body); font-size: 0.87rem; color: var(--muted); width: 130px; flex-shrink: 0; }
.pa-score-bar-bg { flex: 1; height: 5px; background: var(--paper2); border: 1px solid var(--rule-light); overflow: hidden; }
.pa-score-bar-fill { height: 100%; }
.pa-score-num { font-family: var(--mono); font-size: 0.82rem; font-weight: 500; color: var(--ink); width: 36px; text-align: right; flex-shrink: 0; }

/* Indicator list */
.pa-ind-row { display: flex; justify-content: space-between; padding: 0.48rem 0; border-bottom: 1px solid var(--rule-light); }
.pa-ind-row:last-child { border-bottom: none; }
.pa-ind-key { font-family: var(--body); font-size: 0.87rem; color: var(--muted); }
.pa-ind-val { font-family: var(--mono); font-size: 0.88rem; font-weight: 500; color: var(--ink); }
.pa-ind-val.warn { color: var(--red); }

/* Claim card */
.pa-claim {
  background: var(--paper3); border-top: 1px solid var(--rule-light);
  border-left: 4px solid transparent; padding: 0.9rem 1rem; margin-bottom: 1px;
}
.pa-claim.high   { border-left-color: var(--red); }
.pa-claim.medium { border-left-color: var(--amber); }
.pa-claim.low    { border-left-color: var(--green); }
.pa-claim-eyebrow { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.42rem; }
.pa-claim-num { font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); }
.pa-claim-badge { font-family: var(--mono); font-size: 0.6rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.15rem 0.5rem; border: 1px solid; }
.pa-claim-badge.high   { color: var(--red);   border-color: var(--red);   background: var(--red-bg); }
.pa-claim-badge.medium { color: var(--amber); border-color: var(--amber); background: var(--amber-bg); }
.pa-claim-badge.low    { color: var(--green); border-color: var(--green); background: var(--green-bg); }
.pa-claim-body { font-family: var(--body); font-size: 0.91rem; line-height: 1.55; color: var(--ink); margin-bottom: 0.38rem; }
.pa-claim-reason { font-family: var(--mono); font-size: 0.68rem; color: var(--muted); padding-top: 0.35rem; border-top: 1px solid var(--rule-light); }

/* Badges */
.pa-badge { display: inline-block; font-family: var(--mono); font-size: 0.65rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.2rem 0.55rem; border: 1px solid; }
.pa-badge.strong   { color: var(--green); border-color: var(--green); background: var(--green-bg); }
.pa-badge.moderate { color: var(--amber); border-color: var(--amber); background: var(--amber-bg); }
.pa-badge.weak     { color: var(--red);   border-color: var(--red);   background: var(--red-bg); }

.pa-rule       { border: none; border-top: 1px solid var(--rule-light); margin: 1.4rem 0; }
.pa-rule-heavy { border: none; border-top: 2px solid var(--ink); margin: 1.8rem 0; }

@media (max-width: 900px) {
  .pa-masthead-title { font-size: 2.8rem; }
  .pa-verdict-hl { font-size: 2.1rem; }
  .pa-panel-row { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def ensure_state():
    for k, v in {"article_text":"","article_url":"","use_demo":False,
                 "analysis_complete":False,"analysis_running":False,"analysis":None}.items():
        if k not in st.session_state:
            st.session_state[k] = v

def get_api_key():
    try: return st.secrets["OPENAI_API_KEY"]
    except: return None

def safe_preview(text, limit=220):
    text = " ".join(text.split())
    return text[:limit].rstrip()+"…" if len(text)>limit else text

def risk_css(s): return "high" if s>=75 else "medium" if s>=55 else "low"
def risk_label(s): return "High risk" if s>=75 else "Med risk" if s>=55 else "Low risk"
def score_color(s): return "var(--green)" if s>=75 else "var(--amber)" if s>=55 else "var(--red)"
def verdict_class(st_): return {"Publish":"publish","Revise":"revise"}.get(st_,"review")
def verdict_headline(st_): return {"Publish":"Clear to Publish","Revise":"Revision Required"}.get(st_,"Escalate for Review")

def claim_reason(claim, ctype, score):
    if ctype in ["Predictive","Interpretive","Causal"]: return "Forward-looking or interpretive — explicit qualification needed."
    if ctype == "Attributed allegation": return "Attribution quality is the primary editorial risk factor."
    if score >= 75: return "High-impact claim — solid evidence required before publication."
    if score >= 55: return "Material claim warranting a closer sourcing check."
    return "Comparatively lower risk among extracted claims."

def top_risk_claims(claims, article_text, indicators, n=6):
    rows = [{"i":i,"claim":c,"score":claim_risk_score(c,article_text,indicators),"type":classify_claim_type(c)}
            for i,c in enumerate(claims,1)]
    rows.sort(key=lambda x:x["score"],reverse=True)
    return rows[:n]

def run_full_analysis(client, article_text):
    indicators     = compute_indicators(article_text)
    ind_scores     = indicator_based_scores(indicators)
    raw_sc, llm_sc = press_scorecard(client, article_text)
    final_sc       = merge_scores(llm_sc, ind_scores, llm_weight=0.7)
    avg            = average_score(final_sc)
    claims         = extract_claims(client, article_text)
    dec_text       = editorial_decision(client, article_text)
    miss_text      = analyze_missing_perspectives(client, article_text)
    sth_text       = stakeholder_review(client, article_text)
    verdict        = final_editorial_verdict(final_sc, indicators, claims, article_text)
    hl_label, hl_reason = headline_body_consistency(article_text)
    return dict(
        indicators=indicators, ind_scores=ind_scores, raw_sc=raw_sc,
        llm_sc=llm_sc, final_sc=final_sc, avg=avg,
        quality=risk_badge_label(avg),
        hint=decision_hint_from_scores(final_sc),
        claims=claims, dec_text=dec_text, miss_text=miss_text,
        sth_text=sth_text, verdict=verdict,
        hl_label=hl_label, hl_reason=hl_reason,
    )

# ─────────────────────────────────────────────────────────────────────────────
# State + Sidebar
# ─────────────────────────────────────────────────────────────────────────────
ensure_state()

with st.sidebar:
    st.markdown(
        '<div style="font-family:\'Playfair Display\',serif;font-size:1.4rem;font-weight:900;'
        'color:#f5f0e8;padding:0.9rem 0 0.3rem;letter-spacing:-0.01em">'
        'Press<span style="color:#c0161e">Analyzer</span></div>'
        '<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;letter-spacing:0.16em;'
        'text-transform:uppercase;color:#555;border-bottom:1px solid #2a2a2a;padding-bottom:0.8rem;'
        'margin-bottom:0.9rem">Editorial Review System</div>',
        unsafe_allow_html=True,
    )

    secret_key = get_api_key()
    if secret_key:
        st.success("API key loaded", icon="🔑")
        api_key = secret_key
    else:
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")

    st.markdown('<div style="height:0.3rem"></div>', unsafe_allow_html=True)
    input_mode  = st.radio("Input mode",  ["Paste article text","Article URL"], index=1)
    review_mode = st.radio("Workspace",   ["Editor (compact)","Analyst (full)"], index=0)
    st.markdown('<hr style="border-color:#222;margin:0.9rem 0">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;letter-spacing:0.14em;'
                'text-transform:uppercase;color:#555;margin-bottom:0.5rem">Demo Article</div>',
                unsafe_allow_html=True)
    if st.button("Load Demo Article", use_container_width=True):
        st.session_state.update({"article_text":DEMO_ARTICLE,"use_demo":True,
                                  "analysis_complete":False,"analysis_running":False,"analysis":None})
        st.rerun()
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.58rem;color:#3a3a3a;'
                'margin-top:1.2rem;line-height:1.6">Supports public article URLs.<br>'
                'Paywalled pages may extract partially.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Masthead
# ─────────────────────────────────────────────────────────────────────────────
today_str = date.today().strftime("%A, %B %-d, %Y")

st.markdown(f"""
<div class="pa-masthead">
  <div class="pa-masthead-dateline">{today_str} &nbsp;·&nbsp; Pre-Publication Editorial Review System &nbsp;·&nbsp; Prototype</div>
  <div class="pa-masthead-title">Press<span>Analyzer</span></div>
  <hr class="pa-masthead-hrule">
  <hr class="pa-masthead-hrule2">
  <div class="pa-masthead-deck">AI-assisted newsroom audit &mdash; claim risk triage, sourcing analysis, balance scoring &amp; editorial decision support</div>
  <div class="pa-masthead-chips">
    <span class="pa-masthead-chip">Claim Risk Triage</span>
    <span class="pa-masthead-chip">Sourcing Audit</span>
    <span class="pa-masthead-chip">Balance Scoring</span>
    <span class="pa-masthead-chip">Missing Voices</span>
    <span class="pa-masthead-chip">Editorial Panel Simulation</span>
    <span class="pa-masthead-chip">Neutral Rewrite</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Input
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="pa-section">Submit Article for Review</div>', unsafe_allow_html=True)

col_in, col_guide = st.columns([2.5, 1], gap="large")
with col_in:
    if input_mode == "Paste article text":
        txt = st.text_area("Article text", value=st.session_state.get("article_text",""),
                           height=260, placeholder="Paste full article text here…", label_visibility="collapsed")
        st.session_state["article_text"] = txt
    else:
        url = st.text_input("Article URL", value=st.session_state.get("article_url",""),
                            placeholder="https://www.reuters.com/…", label_visibility="collapsed")
        st.session_state["article_url"] = url
        if url.strip():
            try:
                extracted = extract_article_from_url(url.strip())
                st.session_state["article_text"] = extracted
                st.success(f"Extracted {len(extracted.split())} words from URL.")
                with st.expander("Preview extracted text"):
                    st.write(extracted[:3000])
            except Exception as e:
                st.error(f"Extraction failed: {e}")
    run_btn = st.button("▶  Run Editorial Audit", use_container_width=True)

with col_guide:
    st.markdown("""
<div class="pa-box">
  <div class="pa-box-head">Audit covers</div>
  <div class="pa-ind-row"><span class="pa-ind-key" style="font-weight:600;color:var(--ink)">Sourcing</span><span class="pa-ind-val" style="font-size:0.78rem;color:var(--muted)">Attribution density</span></div>
  <div class="pa-ind-row"><span class="pa-ind-key" style="font-weight:600;color:var(--ink)">Balance</span><span class="pa-ind-val" style="font-size:0.78rem;color:var(--muted)">Stakeholder coverage</span></div>
  <div class="pa-ind-row"><span class="pa-ind-key" style="font-weight:600;color:var(--ink)">Tone</span><span class="pa-ind-val" style="font-size:0.78rem;color:var(--muted)">Loaded language</span></div>
  <div class="pa-ind-row"><span class="pa-ind-key" style="font-weight:600;color:var(--ink)">Transparency</span><span class="pa-ind-val" style="font-size:0.78rem;color:var(--muted)">Fact vs. inference</span></div>
  <div class="pa-ind-row" style="border-bottom:none"><span class="pa-ind-key" style="font-weight:600;color:var(--ink)">Claims</span><span class="pa-ind-val" style="font-size:0.78rem;color:var(--muted)">Per-claim risk score</span></div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────
article_text = st.session_state.get("article_text","")

if run_btn:
    if not api_key:
        st.warning("Please enter an OpenAI API key."); st.stop()
    if len(article_text.strip()) < 250:
        st.warning("Article too short — please provide at least a few paragraphs."); st.stop()
    st.session_state.update({"analysis_running":True,"analysis_complete":False,"analysis":None})
    with st.status("Running editorial analysis…", expanded=True) as sb:
        st.write("Computing structural indicators…")
        st.write("Scoring sourcing, balance, tone, transparency…")
        st.write("Extracting high-impact claims…")
        st.write("Running missing-perspectives & panel review…")
        result = run_full_analysis(get_client(api_key), article_text)
        sb.update(label="Analysis complete ✓", state="complete")
    st.session_state.update({"analysis":result,"analysis_running":False,"analysis_complete":True})

# ─────────────────────────────────────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.get("analysis_complete") and st.session_state.get("analysis"):
    d   = st.session_state["analysis"]
    v   = d["verdict"]
    fs  = d["final_sc"]
    ind = d["indicators"]
    claims = d["claims"]
    top = top_risk_claims(claims, article_text, ind, n=6)
    vc  = verdict_class(v["status"])
    hl_cls = d["hl_label"].lower() if d["hl_label"].lower() in ("strong","moderate","weak") else "moderate"

    st.markdown('<div class="pa-rule-heavy"></div>', unsafe_allow_html=True)

    # ── VERDICT ──────────────────────────────────────────────────────────────
    st.markdown('<div class="pa-section">Editorial Verdict</div>', unsafe_allow_html=True)

    chips_html = "".join([
        f'<div class="pa-vchip">{k} <b>{val}</b></div>'
        for k, val in [("Severity", v['severity']), ("Confidence", v['confidence']),
                       ("Quality", d['quality']), ("Avg score", d['avg'] or "N/A"),
                       ("Headline/body", d['hl_label']), ("Claims found", len(claims))]
    ])
    st.markdown(f"""
<div class="pa-verdict {vc}">
  <div class="pa-verdict-eyebrow">Final Editorial Decision</div>
  <div class="pa-verdict-hl">{verdict_headline(v['status'])}</div>
  <hr class="pa-verdict-rule">
  <div class="pa-verdict-hint">{d['hint']}</div>
  <div class="pa-verdict-chips">{chips_html}</div>
</div>""", unsafe_allow_html=True)

    # ── 3 panels ─────────────────────────────────────────────────────────────
    b_li  = "".join(f"<li>{x}</li>" for x in (v["blocking_issues"]     or ["No blocking issues detected."]))
    r_li  = "".join(f"<li>{x}</li>" for x in (v["required_actions"]    or ["No mandatory actions."]))
    nb_li = "".join(f"<li>{x}</li>" for x in (v["non_blocking_issues"] or ["No non-blocking notes."]))

    st.markdown(f"""
<div class="pa-panel-row">
  <div class="pa-panel"><div class="pa-panel-head">🚫 Blocking Issues</div><ul>{b_li}</ul></div>
  <div class="pa-panel"><div class="pa-panel-head">🔧 Required Actions</div><ul>{r_li}</ul></div>
  <div class="pa-panel"><div class="pa-panel-head">ℹ Non-Blocking Notes</div><ul>{nb_li}</ul></div>
</div>""", unsafe_allow_html=True)

    # ── SCORES + INDICATORS ───────────────────────────────────────────────────
    st.markdown('<div class="pa-section">Quality Scores &amp; Text Indicators</div>', unsafe_allow_html=True)
    sc_col, ind_col = st.columns([1,1], gap="large")

    with sc_col:
        bars_html = ""
        for label in ["Balance","Sourcing","Tone Neutrality","Transparency"]:
            s = fs.get(label)
            if s is None:
                bars_html += f'<div class="pa-score-row"><div class="pa-score-lbl">{label}</div><div class="pa-score-bar-bg" style="flex:1"></div><div class="pa-score-num">—</div></div>'
            else:
                col = score_color(s)
                bars_html += f"""
<div class="pa-score-row">
  <div class="pa-score-lbl">{label}</div>
  <div class="pa-score-bar-bg"><div class="pa-score-bar-fill" style="width:{s}%;background:{col}"></div></div>
  <div class="pa-score-num">{s}</div>
</div>"""
        st.markdown(f"""
<div class="pa-box">
  <div class="pa-box-head">Merged Scores — LLM 70% + Indicators 30%</div>
  {bars_html}
  <div style="margin-top:1rem;padding-top:0.9rem;border-top:1px solid var(--rule-light)">
    <div style="font-family:var(--mono);font-size:0.62rem;letter-spacing:0.16em;text-transform:uppercase;color:var(--muted);margin-bottom:0.45rem">Headline / Body Consistency</div>
    <span class="pa-badge {hl_cls}">{d['hl_label']}</span>
    <div style="font-family:var(--body);font-style:italic;font-size:0.83rem;color:var(--muted);margin-top:0.5rem;line-height:1.55">{d['hl_reason']}</div>
  </div>
</div>""", unsafe_allow_html=True)

    with ind_col:
        ind_data = [
            ("Quotes",            "quotes",            False),
            ("Attributions",      "attributions",      ind.get("attributions",0)<2),
            ("Numbers",           "numbers",           False),
            ("Loaded words",      "loaded_words",      ind.get("loaded_words",0)>=3),
            ("Hedges",            "hedges",            False),
            ("Named sources",     "named_sources",     ind.get("named_sources",0)<2),
            ("Stakeholder hints", "stakeholder_hints", False),
        ]
        rows_html = ""
        for label, key, warn in ind_data:
            val = ind.get(key,0)
            cls = " warn" if warn else ""
            note = " ⚠" if warn else ""
            rows_html += f'<div class="pa-ind-row"><span class="pa-ind-key">{label}</span><span class="pa-ind-val{cls}">{val}{note}</span></div>'

        st.markdown(f"""
<div class="pa-box">
  <div class="pa-box-head">Deterministic Text Indicators</div>
  {rows_html}
  <div style="font-family:var(--mono);font-size:0.62rem;color:var(--muted);margin-top:0.8rem;padding-top:0.6rem;border-top:1px solid var(--rule-light)">
    ⚠ marks values outside recommended thresholds
  </div>
</div>""", unsafe_allow_html=True)

    # ── CLAIM RISK MAP ────────────────────────────────────────────────────────
    st.markdown('<div class="pa-section">Claim Risk Map</div>', unsafe_allow_html=True)

    if not top:
        st.info("No claims were extracted from this article.")
    else:
        col_a, col_b = st.columns(2, gap="large")
        for col, batch in [(col_a, top[:3]), (col_b, top[3:])]:
            with col:
                for row in batch:
                    css   = risk_css(row["score"])
                    badge = risk_label(row["score"])
                    why   = claim_reason(row["claim"], row["type"], row["score"])
                    st.markdown(f"""
<div class="pa-claim {css}">
  <div class="pa-claim-eyebrow">
    <span class="pa-claim-num">#{row['i']} &nbsp;·&nbsp; {row['type']}</span>
    <span class="pa-claim-badge {css}">{badge} · {row['score']}/100</span>
  </div>
  <div class="pa-claim-body">{safe_preview(row['claim'],230)}</div>
  <div class="pa-claim-reason">{why}</div>
</div>""", unsafe_allow_html=True)

    # ── DEEP ANALYSIS ─────────────────────────────────────────────────────────
    st.markdown('<div class="pa-section">Deep Analysis</div>', unsafe_allow_html=True)

    compact = "Editor" in review_mode
    tab_labels = (["Missing Perspectives","Editorial Panel","Claim Review","Revision","Raw / Debug"]
                  if compact else
                  ["Decision Report","Missing Perspectives","Editorial Panel","Claim Review","Revision","Indicators","Raw / Debug"])
    tabs = st.tabs(tab_labels)

    def tab_missing(t):
        with t:
            st.subheader("Missing voices, evidence & context")
            st.write(d["miss_text"])

    def tab_panel(t):
        with t:
            st.subheader("Simulated editorial panel")
            st.write(d["sth_text"])

    def tab_claims(t):
        with t:
            st.subheader("Claim-by-claim deep review")
            if not claims: st.info("No claims extracted."); return
            for i, claim in enumerate(claims, 1):
                ctype = classify_claim_type(claim)
                risk  = claim_risk_score(claim, article_text, ind)
                with st.expander(f"Claim {i}  ·  {ctype}  ·  Risk {risk}/100"):
                    st.markdown(f"**Claim:** {claim}")
                    with st.spinner("Analysing…"):
                        res = analyze_claim(get_client(api_key), claim, article_text)
                    st.write(res)

    def tab_revision(t):
        with t:
            st.subheader("Revision support")
            st.markdown("**Priority actions**")
            for item in (v["required_actions"] or ["None."]):
                st.markdown(f"- {item}")
            st.divider()
            if st.button("Generate neutral rewrite"):
                with st.spinner("Generating rewrite…"):
                    rw = rewrite_neutral(get_client(api_key), article_text)
                st.write(rw)
            else:
                st.info("Click to generate a publication-safe rewrite of the article.")

    def tab_raw(t):
        with t:
            st.subheader("Raw outputs & debug")
            st.markdown("**Senior editor decision (LLM)**"); st.write(d["dec_text"])
            st.divider()
            st.markdown("**Raw scorecard**"); st.code(d["raw_sc"])
            st.markdown("**Indicator scores**"); st.json(d["ind_scores"])
            st.markdown("**Final merged scores**"); st.json(d["final_sc"])

    if compact:
        tab_missing(tabs[0]); tab_panel(tabs[1]); tab_claims(tabs[2]); tab_revision(tabs[3]); tab_raw(tabs[4])
    else:
        with tabs[0]:
            st.subheader("Pre-publication decision report")
            st.markdown(f"**Status:** `{v['status']}` &nbsp; **Severity:** `{v['severity']}` &nbsp; **Confidence:** `{v['confidence']}`")
            st.divider()
            for heading, items in [("Blocking issues",v["blocking_issues"]),
                                    ("Non-blocking issues",v["non_blocking_issues"]),
                                    ("Required actions",v["required_actions"])]:
                st.markdown(f"**{heading}**")
                for item in (items or ["None."]): st.markdown(f"- {item}")
            st.divider()
            st.markdown("**LLM senior-editor decision**"); st.write(d["dec_text"])
        tab_missing(tabs[1]); tab_panel(tabs[2]); tab_claims(tabs[3]); tab_revision(tabs[4])
        with tabs[5]:
            st.subheader("Indicators & scoring detail")
            for label, data in [("Raw indicators",d["indicators"]),("Indicator scores",d["ind_scores"]),
                                 ("LLM scores",d["llm_sc"]),("Merged scores",d["final_sc"])]:
                st.markdown(f"**{label}**"); st.json(data)
        tab_raw(tabs[6])

elif st.session_state.get("analysis_running"):
    st.info("Analysis running…")