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
from src.scoring import indicator_based_scores, merge_scores, decision_hint_from_scores
from src.utils import average_score, risk_badge_label


st.set_page_config(
    page_title="PressAnalyzer",
    page_icon="🧠",
    layout="wide",
)


def render_card(title: str, value: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.025));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 18px 18px 14px 18px;
            min-height: 125px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        ">
            <div style="font-size: 0.9rem; opacity: 0.72; margin-bottom: 8px;">{title}</div>
            <div style="font-size: 1.9rem; font-weight: 800; line-height: 1.1; margin-bottom: 8px;">{value}</div>
            <div style="font-size: 0.92rem; opacity: 0.78;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_label(text: str):
    st.markdown(
        f"""
        <div style="
            margin-top: 10px;
            margin-bottom: 10px;
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            opacity: 0.72;
        ">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_bar(label: str, score):
    if score is None:
        st.write(f"**{label}:** N/A")
        return

    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"

    st.markdown(
        f"""
        <div style="margin-bottom: 14px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="font-weight:600;">{label}</span>
                <span style="opacity:0.85;">{score}/100</span>
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


st.markdown(
    """
    <div style="padding-top: 6px; padding-bottom: 8px;">
        <div style="font-size: 3rem; font-weight: 900; line-height: 1.0;">PressAnalyzer</div>
        <div style="font-size: 1.15rem; opacity: 0.82; margin-top: 10px;">
            Editorial decision intelligence for assessing whether a publication meets press quality standards.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_left, hero_right = st.columns([2.2, 1.2])

with hero_left:
    st.markdown(
        """
This tool is designed for **media oversight, newsroom quality teams, and editorial reviewers**.

It does not just ask whether a text feels biased.  
It asks the more useful question:

### **Should this article be published as-is, revised, or manually reviewed — and why?**
"""
    )

with hero_right:
    st.info(
        """
**Review dimensions**
- Balance
- Sourcing
- Tone neutrality
- Transparency
- Missing voices
- Claim risk
"""
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
    st.markdown("### Output modes")
    st.markdown(
        """
- Publication recommendation  
- Claim risk map  
- Missing perspective review  
- Stakeholder simulation  
- Neutral rewrite  
"""
    )

article_text = ""
article_url = ""

render_section_label("Article input")

left, right = st.columns([2.2, 1])

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
                st.error(f"Could not extract article: {str(e)}")

with right:
    st.markdown(
        """
### What makes this useful
- Flags risky claims instead of hiding behind a single score  
- Identifies missing voices, evidence, and context  
- Simulates newsroom review perspectives  
- Produces a concrete editorial action recommendation  
"""
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

    with st.spinner("Generating editorial decision..."):
        decision_text = editorial_decision(client, article_text)

    with st.spinner("Extracting core claims..."):
        claims = extract_claims(client, article_text)

    with st.spinner("Reviewing missing voices and evidence..."):
        missing_text = analyze_missing_perspectives(client, article_text)

    with st.spinner("Simulating editorial panel review..."):
        stakeholder_text = stakeholder_review(client, article_text)

    render_section_label("Executive dashboard")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_card(
            "Publication quality",
            quality_label,
            "Overall readiness based on hybrid scoring.",
        )
    with c2:
        render_card(
            "Average score",
            f"{avg_score if avg_score is not None else 'N/A'}",
            "Merged from deterministic indicators and LLM scoring.",
        )
    with c3:
        render_card(
            "Claims extracted",
            str(len(claims)),
            "Core statements identified for claim-level review.",
        )
    with c4:
        render_card(
            "Decision hint",
            score_hint.split(".")[0],
            "Fast interpretation of the hybrid score profile.",
        )

    st.markdown("### Quality dimensions")
    s1, s2 = st.columns([1.3, 1])

    with s1:
        render_score_bar("Balance", final_scores.get("Balance"))
        render_score_bar("Sourcing", final_scores.get("Sourcing"))
        render_score_bar("Tone Neutrality", final_scores.get("Tone Neutrality"))
        render_score_bar("Transparency", final_scores.get("Transparency"))

    with s2:
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

    tabs = st.tabs(
        [
            "Editorial Decision",
            "Claim Risk Map",
            "Missing Perspectives",
            "Stakeholder Review",
            "Indicators",
            "Neutral Rewrite",
            "Raw LLM Scorecard",
        ]
    )

    with tabs[0]:
        st.subheader("Publication recommendation")
        st.write(decision_text)

    with tabs[1]:
        st.subheader("Claim risk map")
        if not claims:
            st.info("No claims were extracted.")
        else:
            for i, claim in enumerate(claims, start=1):
                with st.expander(f"Claim {i}: {claim}"):
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
        st.subheader("Deterministic indicators")
        st.json(indicators)
        st.markdown("### Indicator-based score contribution")
        st.json(indicator_scores)
        st.markdown("### Final merged scores")
        st.json(final_scores)

    with tabs[5]:
        st.subheader("Neutral rewrite support")
        rewrite_now = st.button("Generate neutral rewrite")
        if rewrite_now:
            with st.spinner("Rewriting..."):
                rewritten = rewrite_neutral(client, article_text)
            st.write(rewritten)
        else:
            st.info("Use this to generate a more neutral and transparent rewrite of the article.")

    with tabs[6]:
        st.subheader("Raw LLM scorecard output")
        st.code(raw_scorecard)

else:
    render_section_label("What this system does")
    info1, info2, info3 = st.columns(3)

    with info1:
        render_card(
            "Claim-centered review",
            "Granular",
            "Breaks a publication into important claims instead of returning one vague label.",
        )

    with info2:
        render_card(
            "Editorial action",
            "Actionable",
            "Recommends whether to publish, revise, or manually review the text.",
        )

    with info3:
        render_card(
            "Explainability",
            "Hybrid",
            "Combines measurable indicators with LLM-based editorial reasoning.",
        )

    st.markdown("### Recommended use cases")
    st.markdown(
        """
- Reviewing a draft article before publication  
- Comparing publication quality across stories  
- Detecting weak sourcing or missing perspectives  
- Supporting newsroom quality and standards teams  
"""
    )