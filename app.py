import streamlit as st
import concurrent.futures
import time

from src.article_extractor import extract_article_from_url
from src.claim_analyzer import get_client, extract_claims, analyze_missing_perspectives, editorial_decision, stakeholder_review, press_scorecard, rewrite_neutral, analyze_claim
from src.indicators import compute_indicators
from src.scoring import indicator_based_scores, merge_scores, decision_hint_from_scores, classify_claim_type, claim_risk_score, headline_body_consistency, final_editorial_verdict
from src.utils import average_score, risk_badge_label
from src.history import save_analysis, load_history, delete_entry

st.set_page_config(page_title="PressAnalyzer", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Mono:wght@400;500&family=Syne:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #0C0C0C !important;
    color: #E8E4DC !important;
    font-family: 'Syne', sans-serif !important;
}

.stApp { background: #0C0C0C !important; }
.main .block-container { padding: 2rem 2.5rem 4rem; max-width: 1400px; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid #1E1E1E !important;
}
[data-testid="stSidebar"] * { color: #A8A39A !important; }
[data-testid="stSidebar"] .stButton button { color: #E8E4DC !important; }

/* Hide default streamlit cruft */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* Typography */
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; color: #E8E4DC !important; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #161616 !important;
    border: 1px solid #2A2A2A !important;
    color: #E8E4DC !important;
    border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #C8B87A !important;
    box-shadow: 0 0 0 2px rgba(200,184,122,0.12) !important;
}

/* Buttons */
.stButton button {
    background: #C8B87A !important;
    color: #0C0C0C !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    transition: all 0.15s ease !important;
}
.stButton button:hover { background: #D4C88E !important; transform: translateY(-1px) !important; }

/* Secondary buttons */
.stButton.secondary button {
    background: transparent !important;
    color: #A8A39A !important;
    border: 1px solid #2A2A2A !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1E1E1E !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #5A5550 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 1.25rem !important;
    transition: all 0.15s !important;
}
.stTabs [aria-selected="true"] {
    color: #C8B87A !important;
    border-bottom: 2px solid #C8B87A !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: #111111 !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 6px !important;
    color: #E8E4DC !important;
    font-family: 'Syne', sans-serif !important;
}
.streamlit-expanderContent {
    background: #111111 !important;
    border: 1px solid #1E1E1E !important;
    border-top: none !important;
}

/* Progress */
.stProgress > div > div { background: #C8B87A !important; }
[data-testid="stProgressBar"] > div { background: #1E1E1E !important; }

/* Spinner */
.stSpinner > div { border-top-color: #C8B87A !important; }

/* Radio */
.stRadio label { color: #A8A39A !important; font-family: 'Syne', sans-serif !important; }
.stRadio [data-testid="stMarkdownContainer"] { color: #A8A39A !important; }

/* Metrics */
[data-testid="stMetric"] { background: #111111 !important; border: 1px solid #1E1E1E !important; border-radius: 8px !important; padding: 1rem !important; }
[data-testid="stMetricLabel"] { color: #5A5550 !important; font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"] { color: #E8E4DC !important; font-family: 'Syne', sans-serif !important; }

/* Alerts */
.stAlert { border-radius: 6px !important; border-left: 3px solid #C8B87A !important; background: #161616 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0C0C0C; }
::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 2px; }

/* Custom component classes */
.pa-hero-word {
    font-family: 'Instrument Serif', serif;
    font-size: clamp(3.5rem, 8vw, 7rem);
    line-height: 0.95;
    color: #E8E4DC;
    letter-spacing: -0.02em;
}
.pa-hero-accent { color: #C8B87A; font-style: italic; }
.pa-mono { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #5A5550; letter-spacing: 0.04em; }
.pa-divider { height: 1px; background: #1E1E1E; margin: 1.5rem 0; }
.pa-card {
    background: #111111;
    border: 1px solid #1E1E1E;
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
}
.pa-card-accent { border-left: 3px solid #C8B87A; }
.pa-badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 3px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.pa-badge-gold { background: rgba(200,184,122,0.15); color: #C8B87A; border: 1px solid rgba(200,184,122,0.3); }
.pa-badge-red { background: rgba(220,80,60,0.12); color: #DC503C; border: 1px solid rgba(220,80,60,0.25); }
.pa-badge-green { background: rgba(80,160,100,0.12); color: #50A064; border: 1px solid rgba(80,160,100,0.25); }
.pa-badge-muted { background: #1A1A1A; color: #5A5550; border: 1px solid #222; }
.pa-score-bar-bg { background: #1A1A1A; border-radius: 2px; height: 3px; margin-top: 6px; }
.pa-step { display: flex; align-items: flex-start; gap: 12px; padding: 10px 0; border-bottom: 1px solid #1A1A1A; }
.pa-step-num { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: #3A3530; min-width: 24px; padding-top: 2px; }
.pa-step-text { font-size: 0.88rem; color: #A8A39A; line-height: 1.5; }
.pa-claim-row { padding: 14px 0; border-bottom: 1px solid #1A1A1A; }
.pa-risk-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 6px; }
.verdict-publish { color: #50A064; }
.verdict-revise { color: #C8B87A; }
.verdict-review { color: #DC503C; }
.history-row { padding: 10px 14px; border: 1px solid #1A1A1A; border-radius: 6px; margin-bottom: 6px; cursor: pointer; transition: border-color 0.15s; }
.history-row:hover { border-color: #2A2A2A; }
</style>
""", unsafe_allow_html=True)


# ── HERO HEADER ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 2rem 0 1rem;">
    <div class="pa-hero-word">Press<span class="pa-hero-accent">Analyzer</span></div>
    <div style="margin-top: 1rem; display: flex; align-items: center; gap: 12px;">
        <span class="pa-badge pa-badge-muted">◈ Editorial Intelligence</span>
        <span class="pa-badge pa-badge-muted">Pre-publication Review</span>
        <span class="pa-badge pa-badge-gold">v2.0</span>
    </div>
    <p style="margin-top: 1.25rem; font-size: 0.95rem; color: #5A5550; max-width: 560px; line-height: 1.7;">
        Hybrid editorial decision engine. Parallel LLM analysis, claim-level risk scoring,
        and structured publication verdicts — built for newsroom-grade quality review.
    </p>
</div>
<div class="pa-divider"></div>
""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="pa-mono" style="margin-bottom:1rem;">◈ REVIEW SETUP</div>', unsafe_allow_html=True)

    secret_key = st.secrets.get("OPENAI_API_KEY", "")
    if secret_key:
        st.success("API key loaded from secrets")
        api_key = secret_key
    else:
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")

    st.markdown('<div class="pa-divider"></div>', unsafe_allow_html=True)

    input_mode = st.radio("Input mode", ["URL", "Paste text"], label_visibility="collapsed")

    st.markdown('<div class="pa-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="pa-mono" style="margin-bottom:0.75rem;">ANALYSIS DEPTH</div>', unsafe_allow_html=True)
    run_claims = st.checkbox("Claim-level deep dive", value=True)
    run_stakeholder = st.checkbox("Editorial panel simulation", value=True)
    run_rewrite = st.checkbox("Pre-generate neutral rewrite", value=False)

    st.markdown('<div class="pa-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="pa-mono" style="margin-bottom:0.75rem;">MODEL STRATEGY</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.78rem; color:#3A3530; line-height:1.6;">Scorecard → gpt-4o<br>Claims/Missing → gpt-4o-mini<br>Panel → gpt-4o-mini</div>', unsafe_allow_html=True)

    st.markdown('<div class="pa-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="pa-mono" style="margin-bottom:0.75rem;">ANALYSIS HISTORY</div>', unsafe_allow_html=True)
    history = load_history()
    if history:
        for entry in history[-5:]:
            col1, col2 = st.columns([4,1])
            with col1:
                st.markdown(f'<div class="pa-mono" style="font-size:0.68rem; color:#3A3530; margin-bottom:2px;">{entry["date"]}</div><div style="font-size:0.8rem; color:#A8A39A; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{entry["title"][:38]}</div>', unsafe_allow_html=True)
            with col2:
                if st.button("×", key=f"del_{entry['id']}"):
                    delete_entry(entry['id'])
                    st.rerun()
    else:
        st.markdown('<div style="font-size:0.8rem; color:#3A3530;">No history yet.</div>', unsafe_allow_html=True)


# ── MAIN CONTENT AREA ─────────────────────────────────────────────────────────
article_text = ""

left_col, right_col = st.columns([1.6, 1])

with left_col:
    if input_mode == "URL":
        url_input = st.text_input("", placeholder="https://www.spiegel.de/...", label_visibility="collapsed")
        if url_input:
            with st.spinner("Extracting article..."):
                try:
                    article_text = extract_article_from_url(url_input)
                    word_count = len(article_text.split())
                    st.markdown(f'<div class="pa-mono" style="margin-top:6px;">{word_count} words extracted ✓</div>', unsafe_allow_html=True)
                    with st.expander("Preview extracted text"):
                        st.write(article_text[:3000] + ("..." if len(article_text) > 3000 else ""))
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
    else:
        article_text = st.text_area("", placeholder="Paste article text here...", height=280, label_visibility="collapsed")

with right_col:
    st.markdown("""
    <div class="pa-card" style="height: 100%;">
        <div class="pa-mono" style="margin-bottom: 1rem;">WHAT THIS DOES</div>
        <div class="pa-step">
            <div class="pa-step-num">01</div>
            <div class="pa-step-text">Extracts & cleans article text with custom parser</div>
        </div>
        <div class="pa-step">
            <div class="pa-step-num">02</div>
            <div class="pa-step-text">Runs 5 parallel LLM analyses simultaneously</div>
        </div>
        <div class="pa-step">
            <div class="pa-step-num">03</div>
            <div class="pa-step-text">Merges hybrid scores (LLM 70% + indicators 30%)</div>
        </div>
        <div class="pa-step">
            <div class="pa-step-num">04</div>
            <div class="pa-step-text">Maps claim-level risk with type classification</div>
        </div>
        <div class="pa-step">
            <div class="pa-step-num">05</div>
            <div class="pa-step-text">Generates structured publication verdict</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="pa-divider"></div>', unsafe_allow_html=True)

run_btn = st.button("◈ Run Editorial Audit", use_container_width=True)

# ── ANALYSIS ENGINE ───────────────────────────────────────────────────────────
if run_btn:
    if not api_key:
        st.error("API key required.")
        st.stop()
    if not article_text or len(article_text.strip()) < 250:
        st.error("Article too short — minimum 250 characters.")
        st.stop()

    client = get_client(api_key)

    # Phase 1: indicators (instant, no API)
    status_container = st.container()
    with status_container:
        progress = st.progress(0)
        status_msg = st.empty()

    status_msg.markdown('<div class="pa-mono">Computing linguistic indicators...</div>', unsafe_allow_html=True)
    indicators = compute_indicators(article_text)
    indicator_scores = indicator_based_scores(indicators)
    progress.progress(10)

    # Phase 2: parallel LLM calls
    status_msg.markdown('<div class="pa-mono">Running parallel LLM analyses (5 simultaneous)...</div>', unsafe_allow_html=True)

    tasks = {
        "scorecard": lambda: press_scorecard(client, article_text, model="gpt-4o"),
        "claims": lambda: extract_claims(client, article_text, model="gpt-4o-mini"),
        "missing": lambda: analyze_missing_perspectives(client, article_text, model="gpt-4o-mini"),
        "decision": lambda: editorial_decision(client, article_text, model="gpt-4o-mini"),
    }
    if run_stakeholder:
        tasks["stakeholder"] = lambda: stakeholder_review(client, article_text, model="gpt-4o-mini")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks.items()}
        done_count = 0
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = None
                st.warning(f"⚠ {name} analysis failed: {e}")
            done_count += 1
            progress.progress(10 + int(done_count / len(tasks) * 75))

    progress.progress(90)
    status_msg.markdown('<div class="pa-mono">Computing verdict...</div>', unsafe_allow_html=True)

    # Unpack results
    raw_scorecard, llm_scores = results.get("scorecard") or ("", {})
    claims = results.get("claims") or []
    missing_text = results.get("missing") or "Analysis unavailable."
    decision_text = results.get("decision") or "Analysis unavailable."
    stakeholder_text = results.get("stakeholder") or "Analysis unavailable."

    # Phase 3: scoring
    final_scores = merge_scores(llm_scores, indicator_scores, llm_weight=0.7)
    avg = average_score(final_scores)
    quality_label = risk_badge_label(avg)
    score_hint = decision_hint_from_scores(final_scores)
    verdict = final_editorial_verdict(final_scores, indicators, claims, article_text)
    consistency_label, consistency_reason = headline_body_consistency(article_text)

    # Optional: neutral rewrite
    rewrite_text = ""
    if run_rewrite:
        status_msg.markdown('<div class="pa-mono">Generating neutral rewrite...</div>', unsafe_allow_html=True)
        rewrite_text = rewrite_neutral(client, article_text)

    progress.progress(100)
    time.sleep(0.3)
    status_container.empty()

    # Save to history
    save_analysis(
        title=article_text[:80].replace("\n", " "),
        url=url_input if input_mode == "URL" else "",
        verdict=verdict["status"],
        avg_score=avg,
        scores=final_scores,
    )

    # ── VERDICT BANNER ────────────────────────────────────────────────────────
    verdict_class = {"Publish": "verdict-publish", "Revise": "verdict-revise"}.get(verdict["status"], "verdict-review")
    st.markdown(f"""
    <div class="pa-card pa-card-accent" style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div class="pa-mono" style="margin-bottom: 8px;">EDITORIAL VERDICT</div>
                <div class="{verdict_class}" style="font-family: 'Instrument Serif', serif; font-size: 3rem; line-height: 1; letter-spacing: -0.02em;">{verdict['status']}</div>
                <div style="margin-top: 10px; font-size: 0.88rem; color: #5A5550; max-width: 480px;">{score_hint}</div>
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <div class="pa-card" style="min-width: 110px; text-align: center;">
                    <div class="pa-mono" style="margin-bottom:6px;">SEVERITY</div>
                    <div style="font-size: 1.5rem; font-weight: 700; font-family: 'Syne', sans-serif;">{verdict['severity']}</div>
                </div>
                <div class="pa-card" style="min-width: 110px; text-align: center;">
                    <div class="pa-mono" style="margin-bottom:6px;">CONFIDENCE</div>
                    <div style="font-size: 1.5rem; font-weight: 700; font-family: 'Syne', sans-serif;">{verdict['confidence']}</div>
                </div>
                <div class="pa-card" style="min-width: 110px; text-align: center;">
                    <div class="pa-mono" style="margin-bottom:6px;">QUALITY</div>
                    <div style="font-size: 1.5rem; font-weight: 700; font-family: 'Syne', sans-serif;">{quality_label}</div>
                </div>
                <div class="pa-card" style="min-width: 110px; text-align: center;">
                    <div class="pa-mono" style="margin-bottom:6px;">AVG SCORE</div>
                    <div style="font-size: 1.5rem; font-weight: 700; font-family: 'Syne', sans-serif;">{avg if avg else 'N/A'}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SCORES + INDICATORS ───────────────────────────────────────────────────
    score_col, ind_col = st.columns([1.2, 1])

    with score_col:
        st.markdown('<div class="pa-mono" style="margin-bottom:1rem;">QUALITY DIMENSIONS</div>', unsafe_allow_html=True)
        for dim, score in final_scores.items():
            if score is None:
                continue
            color = "#50A064" if score >= 75 else "#C8B87A" if score >= 50 else "#DC503C"
            st.markdown(f"""
            <div style="margin-bottom: 16px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="font-size:0.85rem; color:#A8A39A;">{dim}</span>
                    <span style="font-family:'DM Mono',monospace; font-size:0.8rem; color:{color};">{score}/100</span>
                </div>
                <div class="pa-score-bar-bg">
                    <div style="width:{score}%; height:3px; background:{color}; border-radius:2px; transition: width 0.8s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with ind_col:
        st.markdown('<div class="pa-mono" style="margin-bottom:1rem;">LINGUISTIC INDICATORS</div>', unsafe_allow_html=True)
        ind_items = [
            ("Quotes detected", indicators['quotes'], 3, True),
            ("Attribution signals", indicators['attributions'], 4, True),
            ("Named sources", indicators['named_sources'], 3, True),
            ("Numeric references", indicators['numbers'], 5, True),
            ("Loaded words", indicators['loaded_words'], 2, False),
            ("Hedge markers", indicators['hedges'], 3, True),
            ("Stakeholder hints", indicators['stakeholder_hints'], 4, True),
        ]
        for label, val, threshold, higher_is_better in ind_items:
            ok = val >= threshold if higher_is_better else val <= threshold
            badge = "pa-badge-green" if ok else "pa-badge-red"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding: 7px 0; border-bottom: 1px solid #1A1A1A;">
                <span style="font-size:0.83rem; color:#5A5550;">{label}</span>
                <span class="pa-badge {badge}">{val}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="pa-divider"></div>', unsafe_allow_html=True)

    # ── BLOCKERS + ACTIONS ────────────────────────────────────────────────────
    b1, b2, b3 = st.columns(3)
    for col, title, items, empty_txt, accent in [
        (b1, "BLOCKING ISSUES", verdict['blocking_issues'], "None detected", "#DC503C"),
        (b2, "NON-BLOCKING", verdict['non_blocking_issues'], "None detected", "#C8B87A"),
        (b3, "REQUIRED ACTIONS", verdict['required_actions'], "No action required", "#50A064"),
    ]:
        with col:
            st.markdown(f'<div class="pa-mono" style="color:{accent}; margin-bottom:0.75rem;">{title}</div>', unsafe_allow_html=True)
            if items:
                for item in items:
                    st.markdown(f'<div class="pa-step"><div class="pa-step-num">—</div><div class="pa-step-text">{item}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:0.83rem; color:#3A3530;">{empty_txt}</div>', unsafe_allow_html=True)

    st.markdown('<div class="pa-divider"></div>', unsafe_allow_html=True)

    # ── CLAIM MAP ─────────────────────────────────────────────────────────────
    st.markdown(f'<div class="pa-mono" style="margin-bottom:1rem;">CLAIM EVIDENCE MAP — {len(claims)} claims identified</div>', unsafe_allow_html=True)

    if claims:
        for i, claim in enumerate(claims, 1):
            ctype = classify_claim_type(claim)
            risk = claim_risk_score(claim, article_text, indicators)
            rlabel = "High" if risk >= 75 else "Medium" if risk >= 55 else "Low"
            dot_color = "#DC503C" if rlabel == "High" else "#C8B87A" if rlabel == "Medium" else "#50A064"
            badge_cls = "pa-badge-red" if rlabel == "High" else "pa-badge-gold" if rlabel == "Medium" else "pa-badge-green"

            st.markdown(f"""
            <div class="pa-claim-row">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="pa-mono" style="color:#3A3530;">#{i:02d}</span>
                        <span class="pa-badge pa-badge-muted">{ctype}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-family:'DM Mono',monospace; font-size:0.72rem; color:{dot_color};">{risk}/100</span>
                        <span class="pa-badge {badge_cls}">
                            <span class="pa-risk-dot" style="background:{dot_color};"></span>{rlabel}
                        </span>
                    </div>
                </div>
                <div style="font-size:0.9rem; color:#A8A39A; line-height:1.6;">{claim}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="pa-divider"></div>', unsafe_allow_html=True)

    # ── DETAIL TABS ───────────────────────────────────────────────────────────
    tab_labels = ["Full Verdict", "Claim Deep Dive", "Missing Perspectives", "Indicators & Scoring", "Raw Outputs"]
    if run_stakeholder:
        tab_labels.insert(3, "Editorial Panel")
    if run_rewrite:
        tab_labels.append("Neutral Rewrite")

    tabs = st.tabs(tab_labels)
    tab_idx = 0

    with tabs[tab_idx]:
        st.markdown("### Automated verdict summary")
        st.markdown(f"**Status:** {verdict['status']}  \n**Severity:** {verdict['severity']}  \n**Confidence:** {verdict['confidence']}")
        st.markdown("### Headline-body consistency")
        st.markdown(f"**Assessment:** {consistency_label}  \n**Reason:** {consistency_reason}")
        st.markdown("### LLM senior editor decision")
        st.write(decision_text)
    tab_idx += 1

    with tabs[tab_idx]:
        if not claims:
            st.info("No claims extracted.")
        elif not run_claims:
            st.info("Claim deep dive disabled. Enable in sidebar.")
        else:
            for i, claim in enumerate(claims, 1):
                ctype = classify_claim_type(claim)
                risk = claim_risk_score(claim, article_text, indicators)
                with st.expander(f"#{i:02d} · {ctype} · Risk {risk}/100 — {claim[:60]}..."):
                    st.markdown(f"**Full claim:** {claim}")
                    with st.spinner("Analyzing claim..."):
                        result = analyze_claim(client, claim, article_text)
                    st.write(result)
    tab_idx += 1

    with tabs[tab_idx]:
        st.markdown("### Missing voices, evidence & context")
        st.write(missing_text)
    tab_idx += 1

    if run_stakeholder:
        with tabs[tab_idx]:
            st.markdown("### Simulated editorial panel")
            st.write(stakeholder_text)
        tab_idx += 1

    with tabs[tab_idx]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Deterministic indicators")
            st.json(indicators)
            st.markdown("### Indicator-based scores")
            st.json(indicator_scores)
        with c2:
            st.markdown("### LLM scores (raw)")
            st.json(llm_scores)
            st.markdown("### Merged final scores")
            st.json(final_scores)
    tab_idx += 1

    with tabs[tab_idx]:
        st.markdown("### Raw scorecard output")
        st.code(raw_scorecard, language=None)
        st.markdown("### Decision output")
        st.code(decision_text, language=None)
    tab_idx += 1

    if run_rewrite and rewrite_text:
        with tabs[tab_idx]:
            st.markdown("### Neutral rewrite")
            st.write(rewrite_text)

else:
    # ── EMPTY STATE ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 4rem 0; color: #2A2520;">
        <div style="font-family:'Instrument Serif',serif; font-size:5rem; opacity:0.3;">◈</div>
        <div class="pa-mono" style="margin-top:1rem; color:#2A2520;">AWAITING ARTICLE INPUT</div>
    </div>
    """, unsafe_allow_html=True)
