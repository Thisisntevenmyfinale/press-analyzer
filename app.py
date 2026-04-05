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


def get_api_key():
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None


st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 15% 15%, rgba(59,130,246,0.14), transparent 24%),
                radial-gradient(circle at 85% 10%, rgba(99,102,241,0.13), transparent 20%),
                linear-gradient(180deg, #07111f 0%, #08101d 45%, #091423 100%);
            color: #e5edf8;
        }

        .main .block-container {
            max-width: 1260px;
            padding-top: 1.6rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4 {
            color: #f8fbff;
            letter-spacing: -0.02em;
        }

        p, li, div, span {
            color: #d8e3f0;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(7,16,31,0.98), rgba(10,18,35,0.98));
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        .hero {
            border: 1px solid rgba(255,255,255,0.07);
            background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.025));
            border-radius: 26px;
            padding: 28px 28px 24px 28px;
            box-shadow: 0 18px 55px rgba(0,0,0,0.22);
            margin-bottom: 20px;
        }

        .hero-title {
            font-size: 3.0rem;
            font-weight: 900;
            line-height: 1.0;
            margin-bottom: 10px;
        }

        .hero-subtitle {
            font-size: 1.08rem;
            max-width: 900px;
            opacity: 0.9;
            line-height: 1.6;
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 18px;
        }

        .pill {
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.045);
            border-radius: 999px;
            padding: 8px 14px;
            font-size: 0.86rem;
            font-weight: 700;
            color: #dbeafe;
        }

        .section-label {
            margin-top: 6px;
            margin-bottom: 12px;
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #93c5fd;
        }

        .card {
            border: 1px solid rgba(255,255,255,0.07);
            background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.03));
            border-radius: 22px;
            padding: 18px 18px 16px 18px;
            box-shadow: 0 14px 34px rgba(0,0,0,0.18);
            height: 100%;
        }

        .mini-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #93c5fd;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .big-number {
            font-size: 2rem;
            font-weight: 900;
            line-height: 1.0;
            margin-bottom: 8px;
            color: #f8fbff;
        }

        .verdict {
            border: 1px solid rgba(255,255,255,0.08);
            background: linear-gradient(135deg, rgba(15,23,42,0.88), rgba(30,41,59,0.72));
            border-radius: 26px;
            padding: 22px;
            box-shadow: 0 18px 50px rgba(0,0,0,0.24);
            margin-bottom: 16px;
        }

        .verdict-status {
            font-size: 2.35rem;
            font-weight: 900;
            line-height: 1.0;
            margin-bottom: 8px;
        }

        .decision-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 12px;
        }

        .decision-chip {
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 12px 14px;
            min-width: 145px;
        }

        .focus-box {
            border: 1px solid rgba(255,255,255,0.07);
            background: rgba(255,255,255,0.03);
            border-radius: 20px;
            padding: 16px 18px;
            height: 100%;
        }

        .risk-row {
            border: 1px solid rgba(255,255,255,0.07);
            background: rgba(255,255,255,0.03);
            border-radius: 18px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }

        .risk-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 800;
            margin-left: 8px;
        }

        .subtle {
            color: #9fb0c4;
        }

        .divider-space {
            height: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_section_label(text: str):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


def render_card(title: str, value: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="card">
            <div class="mini-label">{title}</div>
            <div class="big-number">{value}</div>
            <div style="font-size:0.94rem; opacity:0.86; line-height:1.5;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_bar(label: str, score: int | None):
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


def bullet_block(items: list[str], empty_text: str):
    if not items:
        st.markdown(f"- {empty_text}")
        return
    for item in items:
        st.markdown(f"- {item}")


def risk_color(score: int) -> str:
    if score >= 75:
        return "#ef4444"
    if score >= 55:
        return "#f59e0b"
    return "#22c55e"


def risk_label(score: int) -> str:
    if score >= 75:
        return "High"
    if score >= 55:
        return "Medium"
    return "Low"


def top_risk_claims(claims: list[str], article_text: str, indicators: dict, top_n: int = 3) -> list[dict]:
    rows = []
    for claim in claims:
        score = claim_risk_score(claim, article_text, indicators)
        rows.append(
            {
                "claim": claim,
                "score": score,
                "level": risk_label(score),
                "type": classify_claim_type(claim),
            }
        )
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[:top_n]


def evidence_health_summary(indicators: dict, final_scores: dict) -> list[str]:
    items = []

    sourcing = final_scores.get("Sourcing", 0) or 0
    transparency = final_scores.get("Transparency", 0) or 0
    named_sources = indicators.get("named_sources", 0)
    attributions = indicators.get("attributions", 0)
    quotes = indicators.get("quotes", 0)

    if sourcing < 60:
        items.append("Sourcing is not strong enough for an easy publish decision.")
    else:
        items.append("Core sourcing signals are present, but may still need validation.")

    if transparency < 60:
        items.append("The article does not clearly separate verified facts from interpretation.")
    else:
        items.append("Transparency is acceptable, but not consistently strong throughout.")

    if named_sources < 2:
        items.append("Very few distinct named sources were detected.")
    else:
        items.append(f"{named_sources} distinct named-source candidates were detected.")

    if attributions == 0 and quotes == 0:
        items.append("Direct attribution language is missing or very weak.")
    elif attributions < 2:
        items.append("Attribution exists, but it is too thin for higher-trust publication.")
    else:
        items.append("There are at least some visible attribution signals in the text.")

    return items[:4]


def reader_impact_summary(verdict: dict, article_text: str, indicators: dict) -> str:
    article_lower = article_text.lower()

    if verdict["status"] == "Review manually":
        return (
            "A reader could interpret the article's strongest claims as more verified and settled "
            "than the visible evidence actually supports."
        )

    if verdict["status"] == "Revise":
        if indicators.get("hedges", 0) == 0:
            return (
                "Readers may come away with stronger certainty than the article's evidence and sourcing justify."
            )
        return (
            "The likely reader takeaway is directionally clear, but some claims may feel more definitive than necessary."
        )

    if "according to" not in article_lower and "said" not in article_lower:
        return "Even if the article is publishable, clearer attribution would further strengthen audience trust."

    return "The article is relatively readable for publication, though some trust signals could still be improved."


st.markdown(
    """
    <div class="hero">
        <div class="hero-title">PressAnalyzer</div>
        <div class="hero-subtitle">
            A hybrid editorial decision-support prototype for pre-publication review.
            It helps editors decide whether a story is ready to publish, needs revision,
            or should be escalated to manual review.
        </div>
        <div class="pill-row">
            <div class="pill">Decision-first workflow</div>
            <div class="pill">Claim risk triage</div>
            <div class="pill">Missing voices detection</div>
            <div class="pill">Headline/body consistency</div>
            <div class="pill">Explainable verdicts</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

intro_left, intro_right = st.columns([1.9, 1.1])

with intro_left:
    st.markdown(
        """
This system is designed for **editorial reviewers, newsroom standards teams, media oversight, and publication-quality review**.

Instead of asking only whether a text *feels biased*, it asks the more useful editorial question:

### **Should this article be published as-is, revised, or escalated — and why?**
"""
    )

with intro_right:
    st.markdown(
        """
        <div class="card">
            <div class="mini-label">Review logic</div>
            <div style="line-height:1.9; font-size:0.98rem;">
                1. Determine final decision<br>
                2. Show top blockers<br>
                3. Prioritize risky claims<br>
                4. Suggest practical fixes<br>
                5. Open deep analysis only if needed
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.sidebar:
    st.header("Review setup")

    secret_api_key = get_api_key()
    if secret_api_key:
        st.success("OpenAI key loaded from secrets")
        api_key = secret_api_key
    else:
        api_key = st.text_input("OpenAI API Key", type="password")

    input_mode = st.radio("Input mode", ["Paste article text", "Article URL"])
    review_mode = st.radio("Review mode", ["Editor", "Analyst"], index=0)

    st.markdown("---")
    st.markdown("### What the prototype emphasizes")
    st.markdown(
        """
- fast editorial decisions  
- top blockers first  
- claim-level risk focus  
- actionable revision guidance  
- optional deep-dive analysis  
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
        <div class="card">
            <div class="mini-label">What a better prototype does</div>
            <div style="line-height:1.8; font-size:0.97rem;">
                • reduces cognitive overload<br>
                • shows the decision first<br>
                • highlights only the most dangerous claims<br>
                • separates blockers from nice-to-have fixes<br>
                • keeps deep analysis available but secondary
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

    with st.spinner("Computing indicators and hybrid scores..."):
        indicators = compute_indicators(article_text)
        indicator_scores = indicator_based_scores(indicators)
        raw_scorecard, llm_scores = press_scorecard(client, article_text)
        final_scores = merge_scores(llm_scores, indicator_scores, llm_weight=0.7)
        avg_score = average_score(final_scores)
        quality_label = risk_badge_label(avg_score)
        score_hint = decision_hint_from_scores(final_scores)

    with st.spinner("Generating editorial outputs..."):
        claims = extract_claims(client, article_text)
        decision_text = editorial_decision(client, article_text)
        missing_text = analyze_missing_perspectives(client, article_text)
        stakeholder_text = stakeholder_review(client, article_text)

    verdict = final_editorial_verdict(final_scores, indicators, claims, article_text)
    top_claims = top_risk_claims(claims, article_text, indicators, top_n=3)
    headline_consistency_label, headline_consistency_reason = headline_body_consistency(article_text)
    evidence_notes = evidence_health_summary(indicators, final_scores)
    reader_impact = reader_impact_summary(verdict, article_text, indicators)

    render_section_label("Level 1 · Final decision")

    st.markdown(
        f"""
        <div class="verdict">
            <div class="mini-label">Final editorial decision</div>
            <div class="verdict-status">{verdict['status']}</div>
            <div style="font-size:1.02rem; max-width:900px; opacity:0.9; line-height:1.6;">
                {score_hint}
            </div>

            <div class="decision-strip">
                <div class="decision-chip">
                    <div class="mini-label">Severity</div>
                    <div style="font-size:1.35rem; font-weight:800;">{verdict['severity']}</div>
                </div>
                <div class="decision-chip">
                    <div class="mini-label">Confidence</div>
                    <div style="font-size:1.35rem; font-weight:800;">{verdict['confidence']}</div>
                </div>
                <div class="decision-chip">
                    <div class="mini-label">Quality label</div>
                    <div style="font-size:1.35rem; font-weight:800;">{quality_label}</div>
                </div>
                <div class="decision-chip">
                    <div class="mini-label">Headline/body</div>
                    <div style="font-size:1.35rem; font-weight:800;">{headline_consistency_label}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown('<div class="focus-box">', unsafe_allow_html=True)
        st.markdown("### Why not publish as-is?")
        bullet_block(verdict["blocking_issues"], "No blocking issue was automatically triggered.")
        st.markdown("</div>", unsafe_allow_html=True)

    with a2:
        st.markdown('<div class="focus-box">', unsafe_allow_html=True)
        st.markdown("### Quick fix plan")
        bullet_block(verdict["required_actions"], "No major revision action was automatically triggered.")
        st.markdown("</div>", unsafe_allow_html=True)

    with a3:
        st.markdown('<div class="focus-box">', unsafe_allow_html=True)
        st.markdown("### Reader impact risk")
        st.markdown(reader_impact)
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_label("Level 2 · Core risk picture")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_card("Average score", f"{avg_score if avg_score is not None else 'N/A'}", "Merged LLM + indicator scoring.")
    with k2:
        render_card("Claims extracted", str(len(claims)), "High-impact statements identified.")
    with k3:
        render_card("Top review mode", review_mode, "Editor view emphasizes action and clarity.")
    with k4:
        render_card("Escalation basis", verdict["status"], "Hybrid rule-based editorial verdict.")

    left_risk, right_risk = st.columns([1.15, 1])

    with left_risk:
        st.markdown("### Top 3 risky claims")
        if not top_claims:
            st.info("No claims were extracted.")
        else:
            for idx, row in enumerate(top_claims, start=1):
                badge_color = risk_color(row["score"])
                st.markdown(
                    f"""
                    <div class="risk-row">
                        <div style="display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; align-items:center;">
                            <div style="font-weight:800;">Claim {idx}</div>
                            <div>
                                <span class="subtle">Type: <strong>{row['type']}</strong></span>
                                <span class="risk-badge" style="background:{badge_color}; color:white;">{row['level']} · {row['score']}/100</span>
                            </div>
                        </div>
                        <div style="margin-top:8px; line-height:1.55;">{row['claim']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with right_risk:
        st.markdown("### Evidence health")
        st.markdown('<div class="focus-box">', unsafe_allow_html=True)
        bullet_block(evidence_notes, "No major evidence signal detected.")
        st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)
        st.markdown("### Headline/body consistency")
        st.markdown(f"**Assessment:** {headline_consistency_label}")
        st.markdown(headline_consistency_reason)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)

        st.markdown("### Quality dimensions")
        st.markdown('<div class="focus-box">', unsafe_allow_html=True)
        render_score_bar("Balance", final_scores.get("Balance"))
        render_score_bar("Sourcing", final_scores.get("Sourcing"))
        render_score_bar("Tone Neutrality", final_scores.get("Tone Neutrality"))
        render_score_bar("Transparency", final_scores.get("Transparency"))
        st.markdown("</div>", unsafe_allow_html=True)

    if review_mode == "Editor":
        render_section_label("Level 3 · Optional deep dive")

        with st.expander("Open detailed review workspace"):
            tabs = st.tabs(
                [
                    "Claim Review",
                    "Missing Perspectives",
                    "Editorial Panel",
                    "Revision Support",
                    "Indicators & Scores",
                    "Raw Outputs",
                ]
            )

            with tabs[0]:
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

            with tabs[1]:
                st.subheader("Missing voices, evidence, and context")
                st.write(missing_text)

            with tabs[2]:
                st.subheader("Simulated editorial panel")
                st.write(stakeholder_text)

            with tabs[3]:
                st.subheader("Revision support")
                st.markdown("### Priority revisions")
                bullet_block(verdict["required_actions"], "No major revision priority detected.")
                rewrite_now = st.button("Generate neutral rewrite")
                if rewrite_now:
                    with st.spinner("Rewriting..."):
                        rewritten = rewrite_neutral(client, article_text)
                    st.write(rewritten)
                else:
                    st.info("Generate a more neutral, transparent, publication-safer rewrite.")

            with tabs[4]:
                st.subheader("Indicators and hybrid scoring")
                st.markdown("### Deterministic indicators")
                st.json(indicators)
                st.markdown("### Indicator-based score contribution")
                st.json(indicator_scores)
                st.markdown("### Final merged scores")
                st.json(final_scores)

            with tabs[5]:
                st.subheader("Raw outputs")
                st.markdown("### Senior-editor verdict")
                st.write(decision_text)
                st.markdown("### Raw scorecard")
                st.code(raw_scorecard)

    else:
        render_section_label("Level 3 · Analyst workspace")

        tabs = st.tabs(
            [
                "Decision Report",
                "Claim Review",
                "Missing Perspectives",
                "Editorial Panel",
                "Indicators & Scores",
                "Revision Support",
                "Raw Outputs",
            ]
        )

        with tabs[0]:
            st.subheader("Pre-publication decision report")
            st.markdown(f"**Status:** {verdict['status']}")
            st.markdown(f"**Severity:** {verdict['severity']}")
            st.markdown(f"**Confidence:** {verdict['confidence']}")
            st.markdown("### Blocking issues")
            bullet_block(verdict["blocking_issues"], "None detected.")
            st.markdown("### Non-blocking issues")
            bullet_block(verdict["non_blocking_issues"], "None detected.")
            st.markdown("### Required actions")
            bullet_block(verdict["required_actions"], "No major action required.")
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
            st.markdown("### Headline/body consistency")
            st.markdown(f"**Assessment:** {headline_consistency_label}")
            st.markdown(headline_consistency_reason)

        with tabs[5]:
            st.subheader("Revision support")
            st.markdown("### Priority revisions")
            bullet_block(verdict["required_actions"], "No major revision priority detected.")
            rewrite_now = st.button("Generate neutral rewrite")
            if rewrite_now:
                with st.spinner("Rewriting..."):
                    rewritten = rewrite_neutral(client, article_text)
                st.write(rewritten)
            else:
                st.info("Generate a more neutral, transparent, publication-safer rewrite.")

        with tabs[6]:
            st.subheader("Raw outputs")
            st.markdown("### Scorecard")
            st.code(raw_scorecard)
            st.markdown("### Editorial decision")
            st.write(decision_text)
            st.markdown("### Missing perspectives")
            st.write(missing_text)
            st.markdown("### Stakeholder review")
            st.write(stakeholder_text)

else:
    render_section_label("How this prototype is structured")

    p1, p2, p3 = st.columns(3)
    with p1:
        render_card(
            "Level 1",
            "Decision first",
            "Show the verdict, top blockers, and fix plan before anything else.",
        )
    with p2:
        render_card(
            "Level 2",
            "Risk triage",
            "Highlight only the most dangerous claims and evidence weaknesses.",
        )
    with p3:
        render_card(
            "Level 3",
            "Deep analysis",
            "Keep full claim review and panel outputs available, but secondary.",
        )

    st.markdown("### Why this version is stronger")
    st.markdown(
        """
- It reduces information overload  
- It feels like a real editorial workflow  
- It prioritizes **decision clarity** over raw output volume  
- It makes the prototype more usable in a newsroom context  
- It keeps advanced analysis available without overwhelming the default view  
"""
    )

    st.markdown("### Strong next-step ideas")
    st.markdown(
        """
- Compare **original vs revised** article versions  
- Add a **headline rewrite assistant**  
- Add a **reader takeaway risk** block per top claim  
- Allow editors to mark claims as **resolved / unresolved**  
- Export a one-page **pre-publication review sheet**  
"""
    )