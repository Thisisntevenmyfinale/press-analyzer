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


DEMO_ARTICLE = """
Die Gier ist zurück an der Wall Street, und sie trägt die Handschrift von Elon Musk und Sam Altman. Während die globale Geopolitik durch den Konflikt im Nahen Osten in den Grundfesten erschüttert wird, bereitet sich die US-Börse auf ein Spektakel vor, das alle bisherigen Dimensionen sprengen könnte. Die Zahlen des ersten Quartals 2026 sprechen eine deutliche Sprache: Das Emissionsvolumen bei Aktienverkäufen schoss um 40 Prozent auf atemberaubende 211 Milliarden Dollar nach oben. Es ist der stärkste Jahresauftakt seit dem Rekordjahr 2021 – ein finanzielles Hochamt inmitten des globalen Chaos.

Doch die eigentliche Prüfung steht erst noch bevor. Der Markt bereitet sich auf den „Urknall“ vor: SpaceX steht kurz davor, an die Börse zu gehen. Mit einer angestrebten Bewertung von bis zu 1,75 Billionen Dollar und einem geplanten Emissionsvolumen von über 75 Milliarden Dollar wäre dies nicht nur ein Börsengang, sondern eine Machtdemonstration des Silicon Valley gegenüber der klassischen Industrie. Es ist der Versuch, den Weltraum endgültig zu kommerzialisieren, während auf der Erde die diplomatischen Drähte glühen.

Hinter dem Weltraum-Giganten SpaceX drängt die nächste Welle der Disruption auf das Parkett. OpenAI und der Konkurrent Anthropic prüfen laut Insidern Listings, die ebenfalls zweistellige Milliardenbeträge in die Kassen spülen sollen. Diese KI-Infrastruktur-Titel erweisen sich als erstaunlich resistent gegenüber der allgemeinen Software-Schwäche, die viele Standardwerte in den letzten Wochen nach unten riss. Investoren scheinen bereit zu sein, geopolitische Risiken auszublenden, solange das Versprechen auf die technologische Singularität lockt.

„Die Widerstandsfähigkeit, die wir in diesem Markt angesichts all der Turbulenzen da draußen gesehen haben, ist ganz bemerkenswert“, so John Kolz, Global Head of Equity Capital Markets bei Barclays. Er bringt das Paradoxon auf den Punkt: Es gebe zwar unzählige Gründe für Investoren, den Hörer erst einmal nicht abzunehmen und abzuwarten, bis sich der Staub gelegt hat. Doch das Gegenteil ist der Fall. Das Kapital drängt mit einer fast schon manischen Intensität in neue Emissionen, als gäbe es kein Morgen nach dem Krieg.

Während in den USA die Tech-Träume die Kurse treiben, zeigt sich in Europa ein deutlich nüchterneres, aber ebenso lukratives Bild. Hier ist das IPO-Geschäft fest in der Hand der Rüstungsindustrie. Der tschechische Verteidigungskonzern CSG markierte mit einem 4,5-Milliarden-Dollar-Börsengang das bisherige Highlight des Quartals. Es ist die bittere ökonomische Realität einer neuen Weltordnung: Wo geschossen wird, verdienen die Ausrüster – und die Anleger greifen beherzt zu.
""".strip()


def get_api_key():
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None


def ensure_state():
    defaults = {
        "article_text": "",
        "article_url": "",
        "use_demo": False,
        "analysis_complete": False,
        "analysis": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


ensure_state()


st.markdown(
    """
    <style>
        :root {
            --bg: #0a0a0a;
            --panel: #111111;
            --panel-2: #151515;
            --ink: #f4f1ea;
            --muted: #b6b1a8;
            --line: rgba(255,255,255,0.14);
            --red: #d72638;
            --green: #17b26a;
            --amber: #f59e0b;
        }

        .stApp {
            background: linear-gradient(180deg, #090909 0%, #0d0d0d 100%);
            color: var(--ink);
        }

        .main .block-container {
            max-width: 1320px;
            padding-top: 1.3rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background: #0c0c0c;
            border-right: 1px solid var(--line);
        }

        h1, h2, h3, h4, h5, p, li, div, span, label {
            color: var(--ink);
        }

        .pa-shell {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, #111111 0%, #0d0d0d 100%);
        }

        .hero {
            padding: 24px 24px 20px 24px;
            margin-bottom: 18px;
        }

        .eyebrow {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #f1d2d6;
            margin-bottom: 8px;
            font-weight: 800;
        }

        .hero-title {
            font-size: 4rem;
            font-weight: 900;
            line-height: 0.95;
            margin-bottom: 12px;
            color: #ffffff;
        }

        .hero-sub {
            max-width: 920px;
            font-size: 1.08rem;
            line-height: 1.6;
            color: var(--muted);
        }

        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 18px;
        }

        .hero-pill {
            border: 1px solid var(--line);
            background: #141414;
            padding: 8px 12px;
            font-size: 0.82rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #f2eeea;
        }

        .section-label {
            margin-top: 8px;
            margin-bottom: 10px;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-weight: 900;
            color: #f1d2d6;
        }

        .news-card {
            border: 1px solid var(--line);
            background: var(--panel);
            padding: 18px 18px 16px 18px;
            margin-bottom: 16px;
        }

        .news-card-tight {
            border: 1px solid var(--line);
            background: var(--panel);
            padding: 14px 14px 12px 14px;
            margin-bottom: 12px;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 900;
            line-height: 1;
            margin-top: 6px;
            color: #ffffff;
        }

        .stat-label {
            font-size: 0.78rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #c7bfb4;
            font-weight: 800;
        }

        .verdict-frontpage {
            border: 2px solid #ffffff;
            background: #0d0d0d;
            padding: 22px 22px 18px 22px;
            margin-bottom: 18px;
        }

        .verdict-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: #f1d2d6;
            font-weight: 900;
            margin-bottom: 8px;
        }

        .verdict-headline {
            font-size: 3.2rem;
            font-weight: 900;
            line-height: 0.96;
            margin-bottom: 10px;
            color: #ffffff;
        }

        .verdict-deck {
            font-size: 1.04rem;
            line-height: 1.6;
            color: #d8d3ca;
            max-width: 950px;
        }

        .meta-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 16px;
        }

        .meta-box {
            border: 1px solid var(--line);
            background: #131313;
            min-width: 150px;
            padding: 12px 14px;
        }

        .meta-box .mini {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #c7bfb4;
            font-weight: 800;
            margin-bottom: 6px;
        }

        .meta-box .big {
            font-size: 1.35rem;
            font-weight: 900;
            color: #ffffff;
        }

        .focus-panel {
            border: 1px solid var(--line);
            background: #121212;
            padding: 16px;
            height: 100%;
        }

        .focus-title {
            font-size: 0.86rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 900;
            color: #ffffff;
            margin-bottom: 12px;
        }

        .focus-panel ul {
            padding-left: 18px;
            margin: 0;
        }

        .focus-panel li {
            margin-bottom: 8px;
            color: #ddd7ce;
            line-height: 1.45;
        }

        .heatmap-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }

        .claim-tile {
            border: 1px solid var(--line);
            padding: 14px;
            min-height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .claim-top {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            align-items: flex-start;
            margin-bottom: 10px;
        }

        .claim-num {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 900;
            color: #c7bfb4;
        }

        .claim-risk {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 900;
            color: #ffffff;
            padding: 4px 8px;
            border: 1px solid rgba(255,255,255,0.16);
        }

        .claim-text {
            font-size: 1rem;
            line-height: 1.5;
            color: #f3eee7;
        }

        .claim-meta {
            margin-top: 12px;
            font-size: 0.82rem;
            color: #d2cbc1;
            line-height: 1.4;
        }

        .ticker {
            border: 1px solid var(--line);
            background: #101010;
            padding: 14px 16px;
            margin-bottom: 14px;
        }

        .ticker-line {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.88rem;
            color: #d8d3ca;
            margin-bottom: 6px;
        }

        .newspaper-rule {
            height: 1px;
            background: var(--line);
            margin: 18px 0;
        }

        .tiny-note {
            color: #b6b1a8;
            font-size: 0.9rem;
        }

        @media (max-width: 1100px) {
            .hero-title {
                font-size: 3rem;
            }
            .verdict-headline {
                font-size: 2.4rem;
            }
            .heatmap-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_section_label(text: str):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


def render_stat_card(label: str, value: str, note: str = ""):
    st.markdown(
        f"""
        <div class="news-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="tiny-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def bullet_lines(items: list[str], fallback: str):
    if not items:
        st.markdown(f"- {fallback}")
        return
    for item in items:
        st.markdown(f"- {item}")


def score_color(score: int) -> str:
    if score >= 75:
        return "#1a1a1a"
    if score >= 55:
        return "#271a00"
    return "#2a0d12"


def score_border(score: int) -> str:
    if score >= 75:
        return "#17b26a"
    if score >= 55:
        return "#f59e0b"
    return "#d72638"


def risk_label(score: int) -> str:
    if score >= 75:
        return "High risk"
    if score >= 55:
        return "Medium risk"
    return "Low risk"


def top_risk_claims(claims: list[str], article_text: str, indicators: dict, top_n: int = 6) -> list[dict]:
    rows = []
    for i, claim in enumerate(claims, start=1):
        score = claim_risk_score(claim, article_text, indicators)
        rows.append(
            {
                "index": i,
                "claim": claim,
                "score": score,
                "type": classify_claim_type(claim),
                "label": risk_label(score),
            }
        )
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[:top_n]


def compact_reason_for_claim(claim: str, claim_type: str, score: int) -> str:
    if claim_type in ["Predictive", "Interpretive", "Causal"]:
        return "This claim contains interpretation or forward-looking logic and needs stronger qualification."
    if claim_type == "Attributed allegation":
        return "This claim depends on attribution quality and should be checked for source clarity."
    if score >= 75:
        return "This claim is high-impact and should not appear overly certain without stronger support."
    if score >= 55:
        return "This claim appears material enough to justify a closer sourcing review."
    return "This claim appears comparatively less risky than the others."


def evidence_health_notes(indicators: dict, final_scores: dict) -> list[str]:
    notes = []

    if final_scores.get("Sourcing", 0) < 60:
        notes.append("Sourcing is not yet strong enough for a comfortable publish decision.")
    else:
        notes.append("Sourcing signals are present, but still deserve editorial validation.")

    if final_scores.get("Transparency", 0) < 60:
        notes.append("The line between fact, inference, and interpretation is not always clear.")
    else:
        notes.append("Transparency is acceptable, though not consistently strong across the text.")

    if indicators.get("attributions", 0) < 2:
        notes.append("Direct attribution language is sparse relative to the article's strongest claims.")
    else:
        notes.append("The article includes at least some visible attribution signals.")

    if indicators.get("hedges", 0) == 0:
        notes.append("Uncertainty markers are mostly absent, which can make interpretation sound too settled.")
    else:
        notes.append("Some uncertainty language is present, which helps calibrate reader expectations.")

    return notes[:4]


def reader_takeaway(verdict: dict, final_scores: dict, indicators: dict) -> str:
    if verdict["status"] == "Review manually":
        return (
            "A reader could treat the story's strongest conclusions as settled fact even though the visible sourcing and "
            "transparency signals are not strong enough for that level of certainty."
        )

    if verdict["status"] == "Revise":
        if final_scores.get("Transparency", 0) < 60:
            return (
                "The likely takeaway is directionally clear, but readers may not easily distinguish reported facts from "
                "narrative interpretation."
            )
        return (
            "The article is broadly understandable, but some framing may feel stronger than the evidence presentation."
        )

    if indicators.get("attributions", 0) < 2:
        return "The story may be publishable, but clearer attribution would still improve audience trust."
    return "The story is comparatively readable for publication, with manageable trust risk."


def verdict_headline(status: str) -> str:
    if status == "Review manually":
        return "ESCALATE TO MANUAL REVIEW"
    if status == "Revise":
        return "REVISION REQUIRED"
    return "READY TO PUBLISH"


def safe_preview(text: str, limit: int = 220) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def run_full_analysis(client, article_text: str):
    indicators = compute_indicators(article_text)
    indicator_scores = indicator_based_scores(indicators)
    raw_scorecard, llm_scores = press_scorecard(client, article_text)
    final_scores = merge_scores(llm_scores, indicator_scores, llm_weight=0.7)
    avg_score = average_score(final_scores)
    quality_label = risk_badge_label(avg_score)
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
        "avg_score": avg_score,
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


st.markdown(
    """
    <div class="pa-shell hero">
        <div class="eyebrow">Editorial Decision Support Prototype</div>
        <div class="hero-title">PressAnalyzer</div>
        <div class="hero-sub">
            A pre-publication review system that helps editors decide whether a story should be published,
            revised, or escalated. Built around decision clarity, claim risk triage, and explainable newsroom logic.
        </div>
        <div class="hero-pills">
            <div class="hero-pill">Decision first</div>
            <div class="hero-pill">Claim risk map</div>
            <div class="hero-pill">Missing voices</div>
            <div class="hero-pill">Editorial panel</div>
            <div class="hero-pill">Revision guidance</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([1.8, 1.2])

with top_left:
    st.markdown(
        """
This prototype is built for **editorial desks, newsroom standards teams, and publication-quality review**.

It does not just ask whether a text seems biased.

### It asks the more useful editorial question:
**Should this article be published, revised, or escalated — and what exactly should happen next?**
"""
    )

with top_right:
    st.markdown(
        """
        <div class="news-card">
            <div class="section-label" style="margin-top:0;">How to use it</div>
            <div style="line-height:1.8;">
                1. Paste article text or a public news URL<br>
                2. Run the audit<br>
                3. Read the frontpage verdict first<br>
                4. Review only the top risks<br>
                5. Open deep analysis if needed
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.sidebar:
    st.header("Setup")

    secret_api_key = get_api_key()
    if secret_api_key:
        st.success("OpenAI key loaded from secrets")
        api_key = secret_api_key
    else:
        api_key = st.text_input("OpenAI API Key", type="password")

    review_mode = st.radio("Workspace mode", ["Editor", "Analyst"], index=0)
    input_mode = st.radio("Input mode", ["Paste article text", "Article URL"], index=1)

    st.markdown("---")
    st.markdown("### Recommended URL types")
    st.markdown(
        """
- Reuters  
- BBC  
- AP  
- public newspaper / magazine articles  
"""
    )

    if st.button("Load demo article", use_container_width=True):
        st.session_state["article_text"] = DEMO_ARTICLE
        st.session_state["use_demo"] = True
        st.session_state["analysis_complete"] = False
        st.session_state["analysis"] = None

render_section_label("Input")

in_left, in_right = st.columns([2.2, 1])

with in_left:
    if input_mode == "Paste article text":
        article_text = st.text_area(
            "Paste article text",
            value=st.session_state.get("article_text", ""),
            height=330,
            placeholder="Paste a full article draft or a copied news story here...",
        )
        st.session_state["article_text"] = article_text
    else:
        article_url = st.text_input(
            "Paste article URL",
            value=st.session_state.get("article_url", ""),
            placeholder="e.g. https://www.reuters.com/world/... or https://www.ft.com/content/...",
        )
        st.session_state["article_url"] = article_url

        if article_url:
            try:
                extracted = extract_article_from_url(article_url)
                st.session_state["article_text"] = extracted
                st.success("Article extracted successfully.")
                st.caption(f"Extracted length: {len(extracted.split())} words")
                with st.expander("Preview extracted text"):
                    st.write(extracted[:5000])
            except Exception as e:
                st.error(f"Could not extract article: {e}")

with in_right:
    st.markdown(
        """
        <div class="news-card">
            <div class="section-label" style="margin-top:0;">Input guidance</div>
            <div style="line-height:1.75;">
                Use a public article URL or paste the full article text directly.
                Public links usually work best. Paywalled or dynamic pages may extract only partially.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("use_demo"):
        st.markdown(
            """
            <div class="news-card-tight">
                <div class="section-label" style="margin-top:0;">Demo mode</div>
                <div class="tiny-note">A built-in sample article is loaded and ready for analysis.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

article_text = st.session_state.get("article_text", "")

run_analysis = st.button("Run Editorial Audit", use_container_width=True)

if run_analysis:
    if not api_key:
        st.warning("Please enter an OpenAI API key or configure Streamlit secrets.")
        st.stop()

    if not article_text or len(article_text.strip()) < 250:
        st.warning("Please provide a longer article.")
        st.stop()

    client = get_client(api_key)

    ticker_placeholder = st.empty()

    with ticker_placeholder.container():
        st.markdown(
            """
            <div class="ticker">
                <div class="ticker-line">[01] Initializing editorial audit...</div>
                <div class="ticker-line">[02] Preparing extraction, scoring, and review agents...</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.status("Running editorial analysis...", expanded=True) as status:
        st.write("Extracting structural indicators")
        st.write("Scoring sourcing, transparency, balance, and tone")
        st.write("Extracting high-impact claims")
        st.write("Running senior editor, missing-perspective, and panel review")
        result = run_full_analysis(client, article_text)
        status.update(label="Analysis complete", state="complete")

    with ticker_placeholder.container():
        st.markdown(
            """
            <div class="ticker">
                <div class="ticker-line">[01] Claim decomposition complete</div>
                <div class="ticker-line">[02] Evidence and transparency scoring complete</div>
                <div class="ticker-line">[03] Editorial verdict generated</div>
                <div class="ticker-line">[04] Risk triage ready</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.session_state["analysis"] = result
    st.session_state["analysis_complete"] = True

if st.session_state.get("analysis_complete") and st.session_state.get("analysis") is not None:
    data = st.session_state["analysis"]

    indicators = data["indicators"]
    indicator_scores = data["indicator_scores"]
    raw_scorecard = data["raw_scorecard"]
    final_scores = data["final_scores"]
    avg_score = data["avg_score"]
    quality_label = data["quality_label"]
    score_hint = data["score_hint"]
    claims = data["claims"]
    decision_text = data["decision_text"]
    missing_text = data["missing_text"]
    stakeholder_text = data["stakeholder_text"]
    verdict = data["verdict"]
    headline_label = data["headline_label"]
    headline_reason = data["headline_reason"]

    top_claims = top_risk_claims(claims, article_text, indicators, top_n=6)
    evidence_notes = evidence_health_notes(indicators, final_scores)
    takeaway = reader_takeaway(verdict, final_scores, indicators)

    render_section_label("Frontpage verdict")

    st.markdown(
        f"""
        <div class="verdict-frontpage">
            <div class="verdict-kicker">Final Editorial Decision</div>
            <div class="verdict-headline">{verdict_headline(verdict['status'])}</div>
            <div class="verdict-deck">
                {score_hint}
            </div>
            <div class="meta-strip">
                <div class="meta-box">
                    <div class="mini">Severity</div>
                    <div class="big">{verdict['severity']}</div>
                </div>
                <div class="meta-box">
                    <div class="mini">Confidence</div>
                    <div class="big">{verdict['confidence']}</div>
                </div>
                <div class="meta-box">
                    <div class="mini">Quality label</div>
                    <div class="big">{quality_label}</div>
                </div>
                <div class="meta-box">
                    <div class="mini">Headline / Body</div>
                    <div class="big">{headline_label}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    focus1, focus2, focus3 = st.columns(3)

    with focus1:
        st.markdown('<div class="focus-panel">', unsafe_allow_html=True)
        st.markdown('<div class="focus-title">Why not publish as-is?</div>', unsafe_allow_html=True)
        bullet_lines(verdict["blocking_issues"], "No blocking issue was automatically triggered.")
        st.markdown("</div>", unsafe_allow_html=True)

    with focus2:
        st.markdown('<div class="focus-panel">', unsafe_allow_html=True)
        st.markdown('<div class="focus-title">Quick fix plan</div>', unsafe_allow_html=True)
        bullet_lines(verdict["required_actions"], "No major revision action was automatically triggered.")
        st.markdown("</div>", unsafe_allow_html=True)

    with focus3:
        st.markdown('<div class="focus-panel">', unsafe_allow_html=True)
        st.markdown('<div class="focus-title">Likely reader takeaway risk</div>', unsafe_allow_html=True)
        st.markdown(takeaway)
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_label("Decision summary")

    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        render_stat_card("Average score", f"{avg_score if avg_score is not None else 'N/A'}", "Merged LLM + indicator score.")
    with stat2:
        render_stat_card("Claims extracted", str(len(claims)), "Material claims identified for triage.")
    with stat3:
        render_stat_card("Workspace", review_mode, "Editor = concise, Analyst = full workspace.")
    with stat4:
        render_stat_card("Escalation basis", verdict["status"], "Hybrid verdict from risk logic.")

    left_col, right_col = st.columns([1.25, 1])

    with left_col:
        st.markdown("### Top risk claims")
        if not top_claims:
            st.info("No claims were extracted.")
        else:
            st.markdown('<div class="heatmap-grid">', unsafe_allow_html=True)
            for row in top_claims:
                bg = score_color(row["score"])
                border = score_border(row["score"])
                why = compact_reason_for_claim(row["claim"], row["type"], row["score"])
                st.markdown(
                    f"""
                    <div class="claim-tile" style="background:{bg}; border-color:{border};">
                        <div>
                            <div class="claim-top">
                                <div class="claim-num">Claim {row['index']}</div>
                                <div class="claim-risk" style="background:{border};">{row['label']} · {row['score']}/100</div>
                            </div>
                            <div class="claim-text">{safe_preview(row['claim'], 180)}</div>
                        </div>
                        <div class="claim-meta">
                            <strong>Type:</strong> {row['type']}<br>
                            <strong>Why it matters:</strong> {why}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("### Evidence & structure")
        st.markdown('<div class="focus-panel">', unsafe_allow_html=True)
        bullet_lines(evidence_notes, "No notable evidence issue was detected.")
        st.markdown('<div class="newspaper-rule"></div>', unsafe_allow_html=True)
        st.markdown("**Headline/body consistency**")
        st.markdown(f"{headline_label} — {headline_reason}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Core quality scores")
        st.markdown('<div class="focus-panel">', unsafe_allow_html=True)
        for label in ["Balance", "Sourcing", "Tone Neutrality", "Transparency"]:
            score = final_scores.get(label)
            if score is None:
                st.write(f"**{label}:** N/A")
            else:
                color = "#17b26a" if score >= 80 else "#f59e0b" if score >= 60 else "#d72638"
                st.markdown(
                    f"""
                    <div style="margin-bottom: 14px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                            <span style="font-weight:800;">{label}</span>
                            <span>{score}/100</span>
                        </div>
                        <div style="width:100%; height:10px; background:#1f1f1f; border:1px solid rgba(255,255,255,0.08);">
                            <div style="width:{score}%; height:100%; background:{color};"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    if review_mode == "Editor":
        render_section_label("Deep analysis")

        with st.expander("Open full review workspace"):
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
                st.subheader("Claim-by-claim review")
                if not claims:
                    st.info("No claims were extracted.")
                else:
                    for i, claim in enumerate(claims, start=1):
                        ctype = classify_claim_type(claim)
                        risk = claim_risk_score(claim, article_text, indicators)
                        with st.expander(f"Claim {i} · {ctype} · {risk}/100"):
                            st.markdown(f"**Claim:** {claim}")
                            with st.spinner("Running detailed claim review..."):
                                claim_result = analyze_claim(get_client(api_key), claim, article_text)
                            st.write(claim_result)

            with tabs[1]:
                st.subheader("Missing voices, evidence, and context")
                st.write(missing_text)

            with tabs[2]:
                st.subheader("Simulated editorial panel")
                st.write(stakeholder_text)

            with tabs[3]:
                st.subheader("Revision support")
                st.markdown("### Priority actions")
                bullet_lines(verdict["required_actions"], "No major revision priority detected.")
                rewrite_now = st.button("Generate neutral rewrite")
                if rewrite_now:
                    with st.spinner("Generating rewrite..."):
                        rewritten = rewrite_neutral(get_client(api_key), article_text)
                    st.write(rewritten)
                else:
                    st.info("Generate a more neutral and publication-safer rewrite.")

            with tabs[4]:
                st.subheader("Indicators and scoring")
                st.markdown("### Deterministic indicators")
                st.json(indicators)
                st.markdown("### Indicator-based score contribution")
                st.json(indicator_scores)
                st.markdown("### Final merged scores")
                st.json(final_scores)

            with tabs[5]:
                st.subheader("Raw outputs")
                st.markdown("### Senior-editor decision")
                st.write(decision_text)
                st.markdown("### Raw scorecard")
                st.code(raw_scorecard)

    else:
        render_section_label("Analyst workspace")

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
            bullet_lines(verdict["blocking_issues"], "None detected.")
            st.markdown("### Non-blocking issues")
            bullet_lines(verdict["non_blocking_issues"], "None detected.")
            st.markdown("### Required actions")
            bullet_lines(verdict["required_actions"], "No major action required.")
            st.markdown("### LLM senior-editor decision")
            st.write(decision_text)

        with tabs[1]:
            st.subheader("Claim-by-claim review")
            if not claims:
                st.info("No claims were extracted.")
            else:
                for i, claim in enumerate(claims, start=1):
                    ctype = classify_claim_type(claim)
                    risk = claim_risk_score(claim, article_text, indicators)
                    with st.expander(f"Claim {i} · {ctype} · {risk}/100"):
                        st.markdown(f"**Claim:** {claim}")
                        with st.spinner("Running detailed claim review..."):
                            claim_result = analyze_claim(get_client(api_key), claim, article_text)
                        st.write(claim_result)

        with tabs[2]:
            st.subheader("Missing voices, evidence, and context")
            st.write(missing_text)

        with tabs[3]:
            st.subheader("Simulated editorial panel")
            st.write(stakeholder_text)

        with tabs[4]:
            st.subheader("Indicators and scoring")
            st.markdown("### Deterministic indicators")
            st.json(indicators)
            st.markdown("### Indicator-based score contribution")
            st.json(indicator_scores)
            st.markdown("### Final merged scores")
            st.json(final_scores)
            st.markdown("### Headline/body consistency")
            st.markdown(f"**Assessment:** {headline_label}")
            st.markdown(headline_reason)

        with tabs[5]:
            st.subheader("Revision support")
            st.markdown("### Priority actions")
            bullet_lines(verdict["required_actions"], "No major revision priority detected.")
            rewrite_now = st.button("Generate neutral rewrite")
            if rewrite_now:
                with st.spinner("Generating rewrite..."):
                    rewritten = rewrite_neutral(get_client(api_key), article_text)
                st.write(rewritten)
            else:
                st.info("Generate a more neutral and publication-safer rewrite.")

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
    render_section_label("Prototype logic")

    p1, p2, p3 = st.columns(3)
    with p1:
        render_stat_card("1", "Decision first", "Frontpage verdict before any deep analysis.")
    with p2:
        render_stat_card("2", "Risk triage", "Only the top claims and blockers are surfaced immediately.")
    with p3:
        render_stat_card("3", "Deep review", "Claim analysis and panel outputs remain available on demand.")

    st.markdown("### What makes this prototype stronger")
    st.markdown(
        """
- It feels like an **editorial desk tool**, not a generic dashboard  
- It prioritizes **publish / revise / escalate** before everything else  
- It turns claim review into a **visual risk map** instead of a text wall  
- It gives a fast **quick-fix plan** instead of only diagnostics  
- It keeps deep analysis available without overwhelming the default view  
"""
    )