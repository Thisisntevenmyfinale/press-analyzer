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


st.set_page_config(
    page_title="PressAnalyzer",
    page_icon="🧠",
    layout="wide",
)


st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.10), transparent 28%),
                radial-gradient(circle at top right, rgba(99, 102, 241, 0.12), transparent 26%),
                linear-gradient(180deg, #071120 0%, #0b1324 45%, #0a1120 100%);
            color: #f3f4f6;
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #f8fafc;
            letter-spacing: -0.02em;
        }

        p, li, div {
            color: #dbe4f0;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(8,15,30,0.96), rgba(10,18,34,0.96));
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        .hero-shell {
            border: 1px solid rgba(255,255,255,0.08);
            background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            border-radius: 28px;
            padding: 28px 30px 26px 30px;
            box-shadow: 0 22px 60px rgba(0,0,0,0.28);
            margin-bottom: 18px;
        }

        .glass-card {
            border: 1px solid rgba(255,255,255,0.08);
            background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.025));
            border-radius: 22px;
            padding: 18px 18px 16px 18px;
            box-shadow: 0 14px 34px rgba(0,0,0,0.22);
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
        }

        .pill {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            color: #dbeafe;
            border-radius: 999px;
            padding: 8px 14px;
            font-size: 0.88rem;
            font-weight: 600;
        }

        .section-label {
            margin-top: 12px;
            margin-bottom: 12px;
            font-size: 0.84rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #93c5fd;
        }

        .score-box {
            border: 1px solid rgba(255,255,255,0.07);
            background: rgba(255,255,255,0.035);
            border-radius: 18px;
            padding: 16px;
            min-height: 110px;
        }

        .verdict-banner {
            border: 1px solid rgba(255,255,255,0.08);
            background: linear-gradient(135deg, rgba(17,24,39,0.88), rgba(30,41,59,0.75));
            border-radius: 24px;
            padding: 20px 22px;
            box-shadow: 0 18px 44px rgba(0,0,0,0.24);
            margin-bottom: 14px;
        }

        .mini-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #93c5fd;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .list-card {
            border: 1px solid rgba(255,255,255,0.07);
            background: rgba(255,255,255,0.03);
            border-radius: 18px;
            padding: 16px 18px;
            height: 100%;
        }

        .risk-claim {
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.03);
            border-radius: 18px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }

        .subtle {
            color: #a5b4cc;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_card(title: str, value: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="glass-card">
            <div style="font-size:0.86rem; opacity:0.72; margin-bottom:8px;">{title}</div>
            <div style="font-size:2rem; font-weight:900; line-height:1.06; margin-bottom:8px;">{value}</div>
            <div style="font-size:0.93rem; opacity:0.82;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_label(text: str):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


def render_score_bar(label: str, score):
    if score is None:
        st.write(f"**{label}:** N/A")
        return

    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"

    st.markdown(
        f"""
        <div style="margin-bottom: 14px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="font-weight:700;">{label}</span>
                <span style="opacity:0.88;">{score}/100</span>
            </div>
            <div style="
                width:100%;
                height:12px;
                background:rgba(255,255,255,0.08);
                border-radius:999px;
                overflow:hidden;
            ">
                <div style="
                    width:{score}%;
                    height:100%;
                    background:{color};
                    border-radius:999px;
                "></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bullets(items: list[str], empty_text: str = "No major issues detected."):
    if not items:
        st.markdown(f"- {empty_text}")
        return
    for item in items:
        st.markdown(f"- {item}")


st.markdown(
    """
    <div class="hero-shell">
        <div style="font-size: 3.25rem; font-weight: 900; line-height: 1.0; margin-bottom: 10px;">PressAnalyzer</div>
        <div style="font-size: 1.12rem; max-width: 980px; opacity: 0.92;">
            Hybrid editorial decision intelligence for assessing whether a publication is ready to publish,
            needs revision, or should be escalated for manual review.
        </div>
        <div class="pill-row">
            <div class="pill">Claim-centered review</div>
            <div class="pill">Editorial escalation logic</div>
            <div class="pill">Missing voices detection</div>
            <div class="pill">Headline-body consistency</div>
            <div class="pill">Explainable publication verdict</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_left, hero_right = st.columns([2.0, 1.1])

with hero_left:
    st.markdown(
        """
This system is designed for **media oversight, newsroom quality teams, standards editors, and editorial reviewers**.

It is **not** just a bias detector.

It supports the much more useful newsroom question:

### **Should this article be published, revised, or escalated to manual review — and why?**
"""
    )

with hero_right:
    st.markdown(
        """
<div class="glass-card">
    <div class="mini-label">Core Review Dimensions</div>
    <div style="line-height:1.9;">
        • Balance<br>
        • Sourcing<br>
        • Tone neutrality<br>
        • Transparency<br>
        • Missing voices<br>
        • Claim-level risk<br>
        • Publication readiness
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

with st.sidebar:
    st.header("Review setup")

    secret_api_key = st.secrets.get("OPENAI_API_KEY", "")
    if secret_api_key:
        st.success("OpenAI key loaded from Streamlit secrets.")
        api_key = secret_api_key
    else:
        api_key = st.text_input("OpenAI API Key", type="password")

    input_mode = st.radio("Input mode", ["Paste article text", "Article URL"])

    st.markdown("---")
    st.markdown("### Review outputs")
    st.markdown(
        """
- Executive verdict  
- Blocking vs non-blocking issues  
- Claim risk map  
- Missing perspectives  
- Editorial panel simulation  
- Revision support  
"""
    )

article_text = ""
article_url = ""

render_section_label("Article input")

left, right = st.columns([2.15, 1])

with left:
    if input_mode == "Paste article text":
        article_text = st.text_area(
            "Paste article text",
            height=320,
            placeholder="Paste the article here...",
        )
    else:
        article_url = st.text_input("Paste article URL")
        if article_url:
            try:
                article_text = extract_article_from_url(article_url)
                st.success("Article extracted successfully.")
                st.caption(f"Extracted length: {len(article_text.split())} words")
                with st.expander("Preview extracted text"):
                    st.write(article_text[:5000])
            except Exception as e:
                st.error(f"Could not extract article: {e}")

with right:
    st.markdown(
        """
<div class="glass-card">
    <div class="mini-label">Why this is stronger</div>
    <div style="line-height:1.85;">
        • Flags blockers, not just scores<br>
        • Separates claim types and risks<br>
        • Surfaces missing evidence and voices<br>
        • Simulates newsroom review roles<br>
        • Produces a practical editorial verdict
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

run_analysis = st.button("Run Editorial Audit", use_container_width=True)

if run_analysis:
    if not api_key:
        st.warning("Please enter an OpenAI API key or configure Streamlit secrets.")
        st.stop()

    if not article_text or len(article_text.strip()) < 250:
        st.warning("Please provide a longer article.")
        st.stop()

    client = get_client(api_key)

    with st.spinner("Computing measurable indicators..."):
        indicators = compute_indicators(article_text)
        indicator_scores = indicator_based_scores(indicators)

    with st.spinner("Scoring publication quality..."):
        raw_scorecard, llm_scores = press_scorecard(client, article_text)
        final_scores = merge_scores(llm_scores, indicator_scores, llm_weight=0.7)
        avg_score = average_score(final_scores)
        quality_label = risk_badge_label(avg_score)
        score_hint = decision_hint_from_scores(final_scores)

    with st.spinner("Extracting core claims..."):
        claims = extract_claims(client, article_text)

    with st.spinner("Generating verdict and review outputs..."):
        decision_text = editorial_decision(client, article_text)
        missing_text = analyze_missing_perspectives(client, article_text)
        stakeholder_text = stakeholder_review(client, article_text)

    verdict = final_editorial_verdict(final_scores, indicators, claims, article_text)
    headline_consistency_label, headline_consistency_reason = headline_body_consistency(article_text)

    render_section_label("Executive verdict")

    st.markdown(
        f"""
        <div class="verdict-banner">
            <div style="display:flex; justify-content:space-between; gap:18px; flex-wrap:wrap;">
                <div>
                    <div class="mini-label">Final editorial verdict</div>
                    <div style="font-size:2.3rem; font-weight:900; line-height:1.05;">{verdict['status']}</div>
                    <div style="margin-top:8px; opacity:0.84;">{score_hint}</div>
                </div>
                <div style="display:flex; gap:14px; flex-wrap:wrap;">
                    <div class="score-box">
                        <div class="mini-label">Severity</div>
                        <div style="font-size:1.45rem; font-weight:800;">{verdict['severity']}</div>
                    </div>
                    <div class="score-box">
                        <div class="mini-label">Confidence</div>
                        <div style="font-size:1.45rem; font-weight:800;">{verdict['confidence']}</div>
                    </div>
                    <div class="score-box">
                        <div class="mini-label">Quality label</div>
                        <div style="font-size:1.45rem; font-weight:800;">{quality_label}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_card("Average score", f"{avg_score if avg_score is not None else 'N/A'}", "Merged from deterministic indicators and LLM scoring.")
    with c2:
        render_card("Claims extracted", str(len(claims)), "Core statements identified for claim-level review.")
    with c3:
        render_card("Headline-body consistency", headline_consistency_label, headline_consistency_reason)
    with c4:
        render_card("Escalation basis", verdict["status"], "Hybrid decision from scores, indicators, and editorial risk logic.")

    st.markdown("### Quality dimensions")
    sx, sy = st.columns([1.25, 1])

    with sx:
        render_score_bar("Balance", final_scores.get("Balance"))
        render_score_bar("Sourcing", final_scores.get("Sourcing"))
        render_score_bar("Tone Neutrality", final_scores.get("Tone Neutrality"))
        render_score_bar("Transparency", final_scores.get("Transparency"))

    with sy:
        st.markdown('<div class="list-card">', unsafe_allow_html=True)
        st.markdown("#### Interpretation")
        st.markdown(score_hint)
        st.markdown("#### Indicator snapshot")
        st.markdown(
            f"""
- Quotes detected: **{indicators['quotes']}**
- Attributions detected: **{indicators['attributions']}**
- Numeric/statistical mentions: **{indicators['numbers']}**
- Distinct named-source candidates: **{indicators['named_sources']}**
- Stakeholder hints: **{indicators['stakeholder_hints']}**
- Loaded words: **{indicators['loaded_words']}**
- Uncertainty markers: **{indicators['hedges']}**
"""
        )
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_label("Editorial blockers and required actions")

    bx, by, bz = st.columns(3)
    with bx:
        st.markdown('<div class="list-card">', unsafe_allow_html=True)
        st.markdown("### Blocking issues")
        render_bullets(verdict["blocking_issues"], "No blocking issue was automatically triggered.")
        st.markdown("</div>", unsafe_allow_html=True)

    with by:
        st.markdown('<div class="list-card">', unsafe_allow_html=True)
        st.markdown("### Non-blocking issues")
        render_bullets(verdict["non_blocking_issues"], "No notable secondary issue was automatically triggered.")
        st.markdown("</div>", unsafe_allow_html=True)

    with bz:
        st.markdown('<div class="list-card">', unsafe_allow_html=True)
        st.markdown("### Required actions")
        render_bullets(verdict["required_actions"], "No major mandatory revision action detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_label("Claim evidence map")

    if not claims:
        st.info("No claims were extracted.")
    else:
        for i, claim in enumerate(claims, start=1):
            ctype = classify_claim_type(claim)
            risk = claim_risk_score(claim, article_text, indicators)
            risk_label = "High" if risk >= 75 else "Medium" if risk >= 55 else "Low"

            st.markdown(
                f"""
                <div class="risk-claim">
                    <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                        <div style="font-weight:800;">Claim {i}</div>
                        <div class="subtle">Type: <strong>{ctype}</strong> · Risk score: <strong>{risk}/100</strong> · Risk level: <strong>{risk_label}</strong></div>
                    </div>
                    <div style="margin-top:8px; font-size:1.02rem;">{claim}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    tabs = st.tabs(
        [
            "Verdict Report",
            "Claim Risk Review",
            "Missing Perspectives",
            "Editorial Panel",
            "Indicators & Scoring",
            "Neutral Rewrite",
            "Raw LLM Outputs",
        ]
    )

    with tabs[0]:
        st.subheader("Pre-publication verdict report")
        st.markdown("### Automated verdict")
        st.markdown(f"**Status:** {verdict['status']}")
        st.markdown(f"**Severity:** {verdict['severity']}")
        st.markdown(f"**Confidence:** {verdict['confidence']}")
        st.markdown("### Blocking issues")
        render_bullets(verdict["blocking_issues"], "None detected.")
        st.markdown("### Non-blocking issues")
        render_bullets(verdict["non_blocking_issues"], "None detected.")
        st.markdown("### Required actions before publication")
        render_bullets(verdict["required_actions"], "No major action required.")
        st.markdown("### LLM senior-editor decision")
        st.write(decision_text)

    with tabs[1]:
        st.subheader("Claim risk review")
        if not claims:
            st.info("No claims were extracted.")
        else:
            for i, claim in enumerate(claims, start=1):
                ctype = classify_claim_type(claim)
                risk = claim_risk_score(claim, article_text, indicators)

                with st.expander(f"Claim {i} · {ctype} · Risk {risk}/100"):
                    st.markdown(f"**Claim:** {claim}")
                    with st.spinner("Analyzing claim..."):
                        claim_result = analyze_claim(client, claim, article_text)
                    st.write(claim_result)

    with tabs[2]:
        st.subheader("Missing voices, evidence, and context")
        st.write(missing_text)

    with tabs[3]:
        st.subheader("Simulated editorial panel")
        st.write(stakeholder_text)

    with tabs[4]:
        st.subheader("Indicators and hybrid scoring")
        st.markdown("### Deterministic indicators")
        st.json(indicators)
        st.markdown("### Indicator-based score contribution")
        st.json(indicator_scores)
        st.markdown("### Final merged scores")
        st.json(final_scores)
        st.markdown("### Headline-body consistency")
        st.markdown(f"**Assessment:** {headline_consistency_label}")
        st.markdown(f"**Reason:** {headline_consistency_reason}")

    with tabs[5]:
        st.subheader("Revision support and neutral rewrite")
        st.markdown("### Recommended revision priorities")
        render_bullets(verdict["required_actions"], "No major revision priorities detected.")
        rewrite_now = st.button("Generate neutral rewrite")
        if rewrite_now:
            with st.spinner("Rewriting..."):
                rewritten = rewrite_neutral(client, article_text)
            st.write(rewritten)
        else:
            st.info("Generate a more neutral, transparent, and publication-safe rewrite.")

    with tabs[6]:
        st.subheader("Raw LLM outputs")
        st.markdown("### Scorecard")
        st.code(raw_scorecard)
        st.markdown("### Editorial Decision")
        st.write(decision_text)
        st.markdown("### Missing Perspectives")
        st.write(missing_text)
        st.markdown("### Stakeholder Review")
        st.write(stakeholder_text)

else:
    render_section_label("What this system does")

    a, b, c = st.columns(3)
    with a:
        render_card(
            "Claim-centered review",
            "Granular",
            "Breaks a publication into high-impact claims instead of returning one vague label.",
        )
    with b:
        render_card(
            "Editorial escalation",
            "Actionable",
            "Recommends whether to publish, revise, or manually review the text.",
        )
    with c:
        render_card(
            "Explainability",
            "Hybrid",
            "Combines measurable indicators, claim risk logic, and LLM editorial reasoning.",
        )

    st.markdown("### Recommended use cases")
    st.markdown(
        """
- Reviewing a draft article before publication  
- Detecting weak sourcing or missing perspectives  
- Escalating risky stories for manual review  
- Supporting newsroom standards and quality teams  
- Comparing editorial readiness across stories  
"""
    )

    st.markdown("### Why this is stronger than a simple classifier")
    st.markdown(
        """
- It evaluates **publication readiness**, not just bias  
- It surfaces **blocking issues vs non-blocking issues**  
- It performs **claim-level risk review**  
- It highlights **missing evidence, context, and voices**  
- It supports a real **editorial decision workflow**
"""
    )