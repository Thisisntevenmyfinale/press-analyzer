import re
from collections import Counter
from typing import Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup
from openai import OpenAI


# =============================================================================
# CONFIG
# =============================================================================

MODEL_NAME = "gpt-4o-mini"

st.set_page_config(
    page_title="PressAnalyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEMO_ARTICLE = """
Die Gier ist zurück an der Wall Street, und sie trägt die Handschrift von Elon Musk und Sam Altman. Während die globale Geopolitik durch den Konflikt im Nahen Osten in den Grundfesten erschüttert wird, bereitet sich die US-Börse auf ein Spektakel vor, das alle bisherigen Dimensionen sprengen könnte. Die Zahlen des ersten Quartals 2026 sprechen eine deutliche Sprache: Das Emissionsvolumen bei Aktienverkäufen schoss um 40 Prozent auf atemberaubende 211 Milliarden Dollar nach oben. Es ist der stärkste Jahresauftakt seit dem Rekordjahr 2021 – ein finanzielles Hochamt inmitten des globalen Chaos.

Doch die eigentliche Prüfung steht erst noch bevor. Der Markt bereitet sich auf den „Urknall" vor: SpaceX steht kurz davor, an die Börse zu gehen. Mit einer angestrebten Bewertung von bis zu 1,75 Billionen Dollar und einem geplanten Emissionsvolumen von über 75 Milliarden Dollar wäre dies nicht nur ein Börsengang, sondern eine Machtdemonstration des Silicon Valley gegenüber der klassischen Industrie.

Hinter dem Weltraum-Giganten SpaceX drängt die nächste Welle der Disruption auf das Parkett. OpenAI und der Konkurrent Anthropic prüfen laut Insidern Listings, die ebenfalls zweistellige Milliardenbeträge in die Kassen spülen sollen. Diese KI-Infrastruktur-Titel erweisen sich als erstaunlich resistent gegenüber der allgemeinen Software-Schwäche.

„Die Widerstandsfähigkeit, die wir in diesem Markt angesichts all der Turbulenzen da draußen gesehen haben, ist ganz bemerkenswert", so John Kolz, Global Head of Equity Capital Markets bei Barclays.

Während in den USA die Tech-Träume die Kurse treiben, zeigt sich in Europa ein deutlich nüchterneres, aber ebenso lukratives Bild. Hier ist das IPO-Geschäft fest in der Hand der Rüstungsindustrie. Der tschechische Verteidigungskonzern CSG markierte mit einem 4,5-Milliarden-Dollar-Börsengang das bisherige Highlight des Quartals.
""".strip()


# =============================================================================
# CSS
# =============================================================================

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --bg: #0b0d10;
  --surface: #12161b;
  --surface-2: #171c23;
  --border: rgba(255,255,255,0.08);
  --border-2: rgba(255,255,255,0.14);
  --text: #edf2f7;
  --muted: #97a3b6;
  --accent: #6ea8fe;
  --green: #2fbf71;
  --amber: #f3a93b;
  --red: #ef5a6f;
}

html, body, .stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Inter', sans-serif !important;
}

.main .block-container {
  max-width: 1220px;
  padding-top: 1.5rem;
  padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border-2);
}

h1, h2, h3, h4, h5, h6, p, div, span, label, li {
  color: var(--text) !important;
}

.stTextInput input, .stTextArea textarea {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border-2) !important;
  border-radius: 12px !important;
}

.stButton > button {
  background: var(--accent) !important;
  color: #08111f !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  padding: 0.65rem 1rem !important;
}

.stButton > button:hover {
  filter: brightness(1.05);
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.5rem !important;
}

.stTabs [data-baseweb="tab"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 0.55rem 0.9rem !important;
}

.stTabs [aria-selected="true"] {
  border-color: var(--accent) !important;
}

.pa-hero {
  background: linear-gradient(180deg, #11161d 0%, #0e1318 100%);
  border: 1px solid var(--border-2);
  border-radius: 18px;
  padding: 1.4rem 1.5rem;
  margin-bottom: 1.2rem;
}

.pa-kicker {
  font-size: 0.78rem;
  color: var(--accent) !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
  margin-bottom: 0.35rem;
}

.pa-title {
  font-size: 2rem;
  font-weight: 800;
  line-height: 1.05;
  margin-bottom: 0.45rem;
}

.pa-subtitle {
  color: var(--muted) !important;
  line-height: 1.6;
  max-width: 850px;
}

.pa-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1rem 1.1rem;
}

.pa-card-title {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted) !important;
  font-weight: 700;
  margin-bottom: 0.65rem;
}

.pa-verdict {
  border-radius: 18px;
  padding: 1.1rem 1.2rem;
  border: 1px solid var(--border-2);
  margin-bottom: 1rem;
}

.pa-verdict.publish {
  background: rgba(47,191,113,0.08);
  border-color: rgba(47,191,113,0.35);
}

.pa-verdict.revise {
  background: rgba(243,169,59,0.08);
  border-color: rgba(243,169,59,0.35);
}

.pa-verdict.review {
  background: rgba(239,90,111,0.08);
  border-color: rgba(239,90,111,0.35);
}

.pa-verdict-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted) !important;
  font-weight: 700;
  margin-bottom: 0.35rem;
}

.pa-verdict-title {
  font-size: 1.7rem;
  font-weight: 800;
  margin-bottom: 0.35rem;
}

.pa-verdict-text {
  color: var(--muted) !important;
  line-height: 1.55;
}

.pa-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.9rem;
}

.pa-chip {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.42rem 0.72rem;
  font-size: 0.8rem;
}

.pa-chip strong {
  color: var(--text) !important;
}

.pa-score-row {
  display: grid;
  grid-template-columns: 140px 1fr 46px;
  gap: 0.7rem;
  align-items: center;
  margin-bottom: 0.7rem;
}

.pa-score-label {
  font-size: 0.92rem;
  color: var(--text) !important;
  font-weight: 600;
}

.pa-score-track {
  height: 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
  border: 1px solid var(--border);
}

.pa-score-fill {
  height: 100%;
  border-radius: 999px;
}

.pa-score-num {
  font-weight: 800;
  text-align: right;
}

.pa-section-head {
  margin-top: 1.3rem;
  margin-bottom: 0.7rem;
  font-size: 1rem;
  font-weight: 800;
}

.pa-list {
  margin: 0;
  padding-left: 1.1rem;
}

.pa-list li {
  margin-bottom: 0.45rem;
  color: var(--text) !important;
  line-height: 1.55;
}

.pa-claim {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid transparent;
  border-radius: 14px;
  padding: 0.95rem 1rem;
  margin-bottom: 0.8rem;
}

.pa-claim.high { border-left-color: var(--red); }
.pa-claim.medium { border-left-color: var(--amber); }
.pa-claim.low { border-left-color: var(--green); }

.pa-claim-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.45rem;
  align-items: center;
}

.pa-claim-type {
  color: var(--muted) !important;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}

.pa-badge {
  font-size: 0.75rem;
  font-weight: 800;
  border-radius: 999px;
  padding: 0.3rem 0.55rem;
}

.pa-badge.high {
  color: var(--red) !important;
  background: rgba(239,90,111,0.12);
  border: 1px solid rgba(239,90,111,0.28);
}

.pa-badge.medium {
  color: var(--amber) !important;
  background: rgba(243,169,59,0.12);
  border: 1px solid rgba(243,169,59,0.28);
}

.pa-badge.low {
  color: var(--green) !important;
  background: rgba(47,191,113,0.12);
  border: 1px solid rgba(47,191,113,0.28);
}

.pa-muted {
  color: var(--muted) !important;
  line-height: 1.55;
}

.pa-help {
  background: rgba(110,168,254,0.08);
  border: 1px solid rgba(110,168,254,0.22);
  border-radius: 14px;
  padding: 0.9rem 1rem;
  color: var(--text) !important;
}

.pa-mini {
  font-size: 0.85rem;
  color: var(--muted) !important;
}

div[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 0.9rem 1rem;
}
</style>
"""

st.markdown(APP_CSS, unsafe_allow_html=True)


# =============================================================================
# PROMPTS
# =============================================================================

CLAIM_EXTRACTION_PROMPT = """
You are an editorial intelligence assistant for pre-publication newsroom review.

Task:
Extract the 5 to 8 most important claims from the article below.

Definition of a claim:
A claim is a concrete factual assertion, allegation, causal statement, statistic,
interpretive assertion, prediction, or evaluative statement that materially affects the article's message.

Rules:
- Keep each claim concise.
- Avoid duplicates.
- Do not include introductory text.
- Return only a numbered list.
- Claims should be understandable independently.
- Prioritize claims that matter most for editorial risk, verification, fairness, or publication readiness.

Article:
{article}
"""

CLAIM_ANALYSIS_PROMPT = """
You are evaluating a journalistic claim using newsroom-quality standards.

Analyze the following claim.

Claim:
{claim}

Article context:
{article}

Return your answer in exactly this structure:

Claim Type: <Factual / Attributed allegation / Interpretive / Causal / Predictive / Evaluative>
Verification Priority: <Low / Medium / High>
Bias Risk: <Low / Medium / High>
Evidence Strength: <Low / Medium / High>
Sourcing Sufficiency: <Low / Medium / High>
Certainty Inflation: <Yes / No>
Emotional Language: <Yes / No>
Missing Perspective: <short phrase>
Potential Harm Sensitivity: <Low / Medium / High>
Editorial Note: <2-4 sentences explaining why this claim is or is not risky for publication>
"""

MISSING_PERSPECTIVES_PROMPT = """
You are a senior editorial reviewer performing a pre-publication standards review.

Read the article and identify what is missing from a press standards perspective.

Focus on:
- missing stakeholder voices
- missing evidence or data
- missing counterarguments
- missing historical or institutional context
- unclear attribution or transparency gaps
- whether the criticized or affected side is missing

Return your answer in exactly this structure:

Missing Voices:
- <bullet>
- <bullet>

Missing Evidence:
- <bullet>
- <bullet>

Missing Context:
- <bullet>
- <bullet>

Transparency Gaps:
- <bullet>
- <bullet>

Most Important Omission:
<1-2 sentences>

Why It Matters:
<2-4 sentences>

Suggested Newsroom Action:
<short recommendation>

Article:
{article}
"""

EDITORIAL_DECISION_PROMPT = """
You are a senior editor deciding whether an article is ready for publication.

You are not just scoring quality. You are making a practical newsroom recommendation.

Article:
{article}

Return your answer in exactly this structure:

Decision: <Publish / Revise / Review manually>
Severity: <Low / Medium / High>

Blocking Issues:
- <bullet>
- <bullet>

Non-Blocking Issues:
- <bullet>
- <bullet>

Reasoning:
- <bullet>
- <bullet>
- <bullet>

Required Actions Before Publication:
- <bullet>
- <bullet>

Confidence: <Low / Medium / High>
"""

REWRITE_NEUTRAL_PROMPT = """
Rewrite the following article to make it more neutral, balanced, transparent, and publication-safe.

Rules:
- preserve the core factual meaning as much as possible
- reduce emotionally loaded or sensational phrasing
- make uncertainty explicit where appropriate
- make attribution clearer
- separate verified facts from interpretation where needed
- do not invent facts
- do not add facts not present in the text
- keep it readable and newsroom-appropriate

Article:
{article}
"""

STAKEHOLDER_REVIEW_PROMPT = """
You are simulating a newsroom review panel for a pre-publication editorial standards check.

Article:
{article}

Provide evaluations from these four perspectives:
1. Public Editor
2. Fact-Checker
3. Audience Trust Reviewer
4. Standards Editor

For each perspective, return:
- Main concern
- Main strength
- Recommended action

Then return a final section:

Panel Disagreement Level: <Low / Medium / High>
Escalation Recommendation: <Publish / Revise / Review manually>
Why: <2-3 sentences>

Format exactly as:

Public Editor
Main concern: ...
Main strength: ...
Recommended action: ...

Fact-Checker
Main concern: ...
Main strength: ...
Recommended action: ...

Audience Trust Reviewer
Main concern: ...
Main strength: ...
Recommended action: ...

Standards Editor
Main concern: ...
Main strength: ...
Recommended action: ...

Panel Disagreement Level: ...
Escalation Recommendation: ...
Why: ...
"""

PRESS_SCORECARD_PROMPT = """
You are scoring an article on newsroom quality dimensions for publication readiness.

Article:
{article}

Return scores from 0 to 100 for these dimensions:
- Balance
- Sourcing
- Tone Neutrality
- Transparency

Then provide one sentence per score.

Format exactly as:

Balance: <0-100> - <sentence>
Sourcing: <0-100> - <sentence>
Tone Neutrality: <0-100> - <sentence>
Transparency: <0-100> - <sentence>
"""


# =============================================================================
# EXTRACTION
# =============================================================================

BAD_PHRASES = [
    "cookie", "cookies", "privacy policy", "privacy notice", "newsletter",
    "subscribe", "sign up", "log in", "accept", "consent",
    "datenschutz", "datenschutzbestimmungen", "abonnieren", "anmelden",
    "akzeptieren", "zustimmen", "política de privacidad", "privacidad",
    "suscribirse", "aceptar", "consentimiento", "politique de confidentialité",
    "confidentialité", "abonnez-vous", "consentement", "informativa sulla privacy",
    "accetta", "política de privacidade", "aceitar",
]

BAD_ATTR_KEYWORDS = [
    "cookie", "consent", "privacy", "gdpr", "newsletter", "subscribe",
    "signup", "login", "paywall", "banner", "modal", "popup", "advert",
    "promo", "recommend", "recommended", "related", "share", "social",
    "menu", "search", "footer", "header", "breadcrumb", "comment",
    "outbrain", "taboola",
]

CONTENT_HINTS = ["article", "content", "post", "story", "entry", "body", "main", "text"]


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _looks_like_junk(text: str) -> bool:
    text = _normalize_whitespace(text)
    lowered = text.lower()
    if not lowered:
        return True
    if len(lowered.split()) < 5:
        return True
    if any(phrase in lowered for phrase in BAD_PHRASES):
        return True
    junk_patterns = [
        r"^menu$", r"^menü$", r"^search$", r"^suche$", r"^home$",
        r"^read more$", r"^weiterlesen$", r"^related articles$", r"^recommended$",
    ]
    return any(re.search(pattern, lowered) for pattern in junk_patterns)


def _deduplicate_paragraphs(paragraphs: list[str]) -> list[str]:
    seen = set()
    cleaned = []
    for p in paragraphs:
        key = p.lower().strip()
        if key not in seen:
            cleaned.append(p)
            seen.add(key)
    return cleaned


def _safe_attr_text(tag) -> str:
    attrs = getattr(tag, "attrs", {}) or {}
    tag_id = attrs.get("id", "") or ""
    tag_class = attrs.get("class", []) or []
    role = attrs.get("role", "") or ""
    aria_label = attrs.get("aria-label", "") or ""
    if isinstance(tag_class, list):
        tag_class = " ".join(str(x) for x in tag_class)
    else:
        tag_class = str(tag_class)
    return f"{tag_id} {tag_class} {role} {aria_label}".lower().strip()


def _remove_bad_nodes(soup: BeautifulSoup) -> None:
    for tag in soup(["script", "style", "noscript", "header", "footer",
                     "nav", "aside", "form", "button", "svg", "iframe"]):
        try:
            tag.decompose()
        except Exception:
            pass

    to_remove = []
    for tag in soup.find_all(True):
        attr_text = _safe_attr_text(tag)
        if attr_text and any(keyword in attr_text for keyword in BAD_ATTR_KEYWORDS):
            to_remove.append(tag)

    for tag in to_remove:
        try:
            tag.decompose()
        except Exception:
            pass


def _get_candidate_roots(soup: BeautifulSoup) -> list:
    roots = []
    for selector in ["article", "main", "[role='main']"]:
        roots.extend(soup.select(selector))
    if roots:
        return roots

    candidate_divs = []
    for div in soup.find_all("div"):
        attr_text = _safe_attr_text(div)
        if any(hint in attr_text for hint in CONTENT_HINTS):
            candidate_divs.append(div)

    return candidate_divs if candidate_divs else [soup]


def _extract_paragraphs(soup: BeautifulSoup) -> list[str]:
    paragraphs = []

    for root in _get_candidate_roots(soup):
        for p in root.find_all("p"):
            text = _normalize_whitespace(p.get_text(" ", strip=True))
            if _looks_like_junk(text):
                continue
            paragraphs.append(text)

    paragraphs = _deduplicate_paragraphs(paragraphs)

    if len(" ".join(paragraphs).split()) < 180:
        extra = []
        for div in soup.find_all("div"):
            text = _normalize_whitespace(div.get_text(" ", strip=True))
            if len(text.split()) < 30:
                continue
            if _looks_like_junk(text):
                continue
            extra.append(text)
        paragraphs = _deduplicate_paragraphs(paragraphs + extra)

    return paragraphs


def extract_article_from_url(url: str) -> str:
    url = _normalize_url(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        ),
        "Accept-Language": "de,en-US;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if "html" not in content_type:
        raise ValueError("URL did not return HTML content.")

    soup = BeautifulSoup(response.text, "lxml")
    _remove_bad_nodes(soup)
    paragraphs = _extract_paragraphs(soup)
    article_text = "\n\n".join(paragraphs).strip()

    if len(article_text) < 250:
        raise ValueError("No sufficiently clean article text could be extracted from this URL.")

    return article_text[:18000]


# =============================================================================
# OPENAI HELPERS
# =============================================================================

def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def run_prompt(client: OpenAI, prompt: str, temperature: float = 0.2) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise editorial analysis assistant for newsroom-quality "
                    "pre-publication review. Be structured, grounded, concise, and avoid hype."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def extract_claims(client: OpenAI, article: str) -> list[str]:
    prompt = CLAIM_EXTRACTION_PROMPT.format(article=article[:12000])
    raw = run_prompt(client, prompt, temperature=0.1)
    return clean_claim_lines(raw)


def analyze_claim(client: OpenAI, claim: str, article: str) -> str:
    prompt = CLAIM_ANALYSIS_PROMPT.format(claim=claim, article=article[:9000])
    return run_prompt(client, prompt, temperature=0.1)


def analyze_missing_perspectives(client: OpenAI, article: str) -> str:
    prompt = MISSING_PERSPECTIVES_PROMPT.format(article=article[:10000])
    return run_prompt(client, prompt, temperature=0.2)


def editorial_decision(client: OpenAI, article: str) -> str:
    prompt = EDITORIAL_DECISION_PROMPT.format(article=article[:10000])
    return run_prompt(client, prompt, temperature=0.2)


def rewrite_neutral(client: OpenAI, article: str) -> str:
    prompt = REWRITE_NEUTRAL_PROMPT.format(article=article[:8000])
    return run_prompt(client, prompt, temperature=0.3)


def stakeholder_review(client: OpenAI, article: str) -> str:
    prompt = STAKEHOLDER_REVIEW_PROMPT.format(article=article[:10000])
    return run_prompt(client, prompt, temperature=0.25)


def press_scorecard(client: OpenAI, article: str) -> tuple[str, dict]:
    prompt = PRESS_SCORECARD_PROMPT.format(article=article[:10000])
    raw = run_prompt(client, prompt, temperature=0.1)
    parsed = parse_scorecard(raw)
    return raw, parsed


# =============================================================================
# INDICATORS
# =============================================================================

ATTRIBUTION_PATTERNS = [
    r"\baccording to\b", r"\bsaid\b", r"\bstated\b", r"\breported\b",
    r"\breports\b", r"\bannounced\b", r"\bclaimed\b", r"\bclaims\b",
    r"\btold\b", r"\bdata from\b", r"\bfigures from\b", r"\bsource[d]?\b",
    r"\blaut\b", r"\bsagte\b", r"\berklärte\b", r"\bberichtete\b", r"\bzufolge\b",
]

HEDGE_PATTERNS = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\ballegedly\b", r"\breportedly\b",
    r"\bappears to\b", r"\bseems to\b", r"\bsuggests\b",
    r"\bkönnte\b", r"\bscheint\b", r"\boffenbar\b", r"\bmöglicherweise\b", r"\bsoll\b",
]

LOADED_WORDS = [
    "outrageous", "shocking", "devastating", "disastrous", "furious", "slam",
    "blasted", "explosive", "chaotic", "radical", "extreme", "massive", "dramatic",
    "dangerous", "scandal", "urknall", "hochgefährlich", "manisch", "panik",
    "machtdemonstration", "atemberaubend", "gnadenlos", "beben",
]

STAKEHOLDER_HINTS = [
    "government", "minister", "official", "company", "union", "workers",
    "residents", "citizens", "police", "court", "judge", "experts", "researchers",
    "activists", "critics", "supporters", "victims", "community", "spokesperson",
    "regierung", "ministerium", "unternehmen", "gewerkschaft", "arbeitnehmer",
    "bürger", "polizei", "gericht", "richter", "experten", "kritiker", "sprecher",
]

STOPWORD_TITLES = {
    "The", "A", "An", "This", "That", "These", "Those",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
    "Der", "Die", "Das", "Ein", "Eine", "Einer", "Einem", "Einen",
    "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag",
    "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
    "September", "Oktober", "November", "Dezember",
}

COMMON_NON_SOURCE_WORDS = {
    "Wall Street", "Silicon Valley", "Nahen Osten", "US Börse", "US Börsengängen",
    "Ersten Quartals", "Global Head", "Equity Capital", "Markets", "Europa",
    "OpenAI", "Anthropic", "SpaceX", "Goldman Sachs", "Barclays", "BNP Paribas",
}


def count_quotes(text: str) -> int:
    straight = text.count('"') // 2
    curly = min(text.count("\u201c"), text.count("\u201d")) + min(text.count("\u201e"), text.count("\u201c"))
    return straight + curly


def count_attributions(text: str) -> int:
    total = 0
    for pattern in ATTRIBUTION_PATTERNS:
        total += len(re.findall(pattern, text, flags=re.IGNORECASE))
    return total


def count_numbers(text: str) -> int:
    return len(re.findall(r"\b\d+(?:[.,]\d+)?%?\b", text))


def count_loaded_words(text: str) -> int:
    lowered = text.lower()
    return sum(lowered.count(word) for word in LOADED_WORDS)


def count_hedges(text: str) -> int:
    total = 0
    for pattern in HEDGE_PATTERNS:
        total += len(re.findall(pattern, text, flags=re.IGNORECASE))
    return total


def extract_named_source_candidates(text: str) -> list[str]:
    candidates = []

    patterns = [
        r"(?:according to|said|stated|reported|announced|claimed|told)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"(?:laut|sagte|erklärte|berichtete|zufolge)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){0,2})",
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(?:said|stated|reported|announced|claimed|told)\b",
        r"\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2})\s+(?:sagte|erklärte|berichtete)\b",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                name = " ".join(part for part in match if part).strip()
            else:
                name = str(match).strip()

            if not name:
                continue

            first = name.split()[0]
            if first in STOPWORD_TITLES:
                continue
            if name in COMMON_NON_SOURCE_WORDS:
                continue
            if len(name.split()) == 1 and len(name) < 4:
                continue

            candidates.append(name)

    cleaned = []
    for name in candidates:
        if any(char.isdigit() for char in name):
            continue
        cleaned.append(name)

    return cleaned


def count_distinct_named_sources(text: str) -> int:
    candidates = extract_named_source_candidates(text)
    counts = Counter(candidates)
    distinct = []
    for candidate, freq in counts.items():
        if len(candidate.split()) >= 2 and freq >= 1:
            distinct.append(candidate)
    return len(set(distinct))


def count_stakeholder_hints(text: str) -> int:
    lowered = text.lower()
    return sum(1 for term in STAKEHOLDER_HINTS if term in lowered)


def compute_indicators(text: str) -> dict:
    return {
        "quotes": count_quotes(text),
        "attributions": count_attributions(text),
        "numbers": count_numbers(text),
        "loaded_words": count_loaded_words(text),
        "hedges": count_hedges(text),
        "named_sources": count_distinct_named_sources(text),
        "stakeholder_hints": count_stakeholder_hints(text),
    }


# =============================================================================
# SCORING
# =============================================================================

def clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(max(low, min(high, round(value))))


def indicator_based_scores(indicators: dict) -> dict:
    quotes = indicators.get("quotes", 0)
    attributions = indicators.get("attributions", 0)
    numbers = indicators.get("numbers", 0)
    loaded_words = indicators.get("loaded_words", 0)
    hedges = indicators.get("hedges", 0)
    named_sources = indicators.get("named_sources", 0)
    stakeholder_hints = indicators.get("stakeholder_hints", 0)

    sourcing = 32 + quotes * 5 + attributions * 5 + named_sources * 5 + min(numbers, 10) * 1.2
    balance = 34 + stakeholder_hints * 5 + min(named_sources, 8) * 2
    transparency = 30 + attributions * 5 + min(hedges, 8) * 3 + min(numbers, 10) * 1.1
    tone = 84 - loaded_words * 6 + min(hedges, 6) * 1.5

    return {
        "Balance": clamp(balance),
        "Sourcing": clamp(sourcing),
        "Tone Neutrality": clamp(tone),
        "Transparency": clamp(transparency),
    }


def merge_scores(llm_scores: dict, indicator_scores: dict, llm_weight: float = 0.7) -> dict:
    keys = ["Balance", "Sourcing", "Tone Neutrality", "Transparency"]
    merged = {}

    for key in keys:
        llm_val = llm_scores.get(key)
        ind_val = indicator_scores.get(key)

        if llm_val is None and ind_val is None:
            merged[key] = None
        elif llm_val is None:
            merged[key] = ind_val
        elif ind_val is None:
            merged[key] = llm_val
        else:
            merged[key] = round(llm_weight * llm_val + (1 - llm_weight) * ind_val)

    return merged


def decision_hint_from_scores(scores: dict) -> str:
    vals = [v for v in scores.values() if isinstance(v, int)]
    if not vals:
        return "Insufficient scoring information."

    avg = sum(vals) / len(vals)
    sourcing = scores.get("Sourcing", 0)
    transparency = scores.get("Transparency", 0)

    if sourcing < 45 or transparency < 45:
        return "The article should be reviewed carefully because sourcing or transparency appears too weak."
    if avg < 60:
        return "The article likely needs revision before publication."
    if avg < 80:
        return "The article appears moderate in quality but still needs editorial tightening."
    return "The article appears comparatively strong on core publication-quality dimensions."


def classify_claim_type(claim: str) -> str:
    text = claim.lower()

    if any(w in text for w in ["will", "could", "may", "might", "expected", "likely", "forecast", "prüfen", "plant"]):
        return "Predictive"
    if any(w in text for w in ["because", "due to", "led to", "caused", "resulted in", "führt", "wegen", "verursacht"]):
        return "Causal"
    if any(w in text for w in ["according to", "said", "claimed", "reported", "alleged", "laut", "zufolge", "insidern"]):
        return "Attributed allegation"
    if any(w in text for w in ["should", "unacceptable", "dangerous", "outrageous", "wrong", "hochgefährlich"]):
        return "Evaluative"
    if any(w in text for w in ["suggests", "appears", "seems", "indicates", "signals", "scheint", "wirkt"]):
        return "Interpretive"
    return "Factual"


def claim_risk_score(claim: str, article_text: str, indicators: dict) -> int:
    score = 34
    claim_lower = claim.lower()
    article_lower = article_text.lower()
    claim_type = classify_claim_type(claim)

    if claim_type in ["Attributed allegation", "Interpretive", "Causal", "Predictive", "Evaluative"]:
        score += 12

    if any(w in claim_lower for w in [
        "attack", "blame", "scandal", "fraud", "corrupt", "illegal",
        "hochgefährlich", "machtdemonstration", "urknall", "manisch", "panik"
    ]):
        score += 12

    if not any(w in claim_lower for w in [
        "according to", "said", "reported", "stated", "announced", "laut", "so", "zufolge"
    ]):
        score += 8

    if any(w in claim_lower for w in [
        "will", "could", "may", "might", "appears", "seems", "suggests",
        "könnte", "scheint", "soll", "prüfen", "plant"
    ]):
        score += 6

    if indicators.get("attributions", 0) < 2:
        score += 8
    if indicators.get("named_sources", 0) < 2:
        score += 8
    if indicators.get("loaded_words", 0) >= 3:
        score += 8

    if ("response" not in article_lower and "statement" not in article_lower
            and "according to" not in article_lower and "laut" not in article_lower):
        score += 6

    return clamp(score)


def headline_candidate(article_text: str) -> str:
    lines = [line.strip() for line in article_text.splitlines() if line.strip()]
    if not lines:
        return ""
    first = lines[0]
    if len(first.split()) <= 18:
        return first
    return " ".join(first.split()[:14])


def headline_body_consistency(article_text: str) -> tuple[str, str]:
    headline = headline_candidate(article_text)
    if not headline:
        return "Unknown", "No clear headline-like opener was available."

    headline_lower = headline.lower()
    body_lower = article_text.lower()

    strong_words = [
        "attack", "shocking", "massive", "blasted", "furious", "dramatic", "explosive",
        "direct attack", "urknall", "hochgefährlich", "manisch", "panik", "machtdemonstration"
    ]
    evidence_words = [
        "according to", "said", "reported", "statement", "data", "document", "confirmed",
        "announced", "laut", "daten", "erklärte", "bericht", "zitat"
    ]

    strong_count = sum(1 for w in strong_words if w in headline_lower)
    evidence_count = sum(1 for w in evidence_words if w in body_lower)

    if strong_count >= 1 and evidence_count < 2:
        return "Weak", "The opening framing appears stronger than the supporting evidence in the article body."
    if strong_count >= 1 and evidence_count >= 2:
        return "Moderate", "The framing is assertive, but the body includes at least some evidence signals."
    return "Strong", "The opening framing does not appear substantially stronger than the body support."


def derive_blocking_issues(scores: dict, indicators: dict, claims: list[str], article_text: str) -> list[str]:
    issues = []

    if scores.get("Sourcing", 100) < 45:
        issues.append("Key claims appear under-sourced for confident publication.")

    if scores.get("Transparency", 100) < 45:
        issues.append("The article does not clearly separate verification, attribution, and interpretation.")

    if indicators.get("named_sources", 0) < 2:
        issues.append("Too few distinct named sources are visible for a strong editorial release decision.")

    if indicators.get("attributions", 0) < 2:
        issues.append("Several important claims are not clearly attributed.")

    high_risk_claims = sum(1 for claim in claims if claim_risk_score(claim, article_text, indicators) >= 75)
    if high_risk_claims >= 2:
        issues.append("Multiple claims carry high publication risk and should be reviewed before release.")

    consistency_label, consistency_reason = headline_body_consistency(article_text)
    if consistency_label == "Weak":
        issues.append(f"Headline-to-body consistency is weak. {consistency_reason}")

    return issues[:4]


def derive_non_blocking_issues(scores: dict, indicators: dict, article_text: str) -> list[str]:
    issues = []

    if scores.get("Balance", 100) < 65:
        issues.append("The article may benefit from more stakeholder balance or counter-positioning.")

    if scores.get("Tone Neutrality", 100) < 70:
        issues.append("Some wording may sound more assertive or loaded than necessary.")

    if indicators.get("hedges", 0) == 0:
        issues.append("Uncertainty is not clearly signaled where interpretation may be involved.")

    if indicators.get("numbers", 0) == 0:
        issues.append("The article contains little visible quantitative support.")

    if ("according to" not in article_text.lower() and "said" not in article_text.lower()
            and "laut" not in article_text.lower()):
        issues.append("Attribution language could be more explicit throughout the piece.")

    return issues[:4]


def required_actions(scores: dict, indicators: dict, claims: list[str], article_text: str) -> list[str]:
    actions = []

    if scores.get("Sourcing", 100) < 60:
        actions.append("Add clearer sourcing or named attribution to the highest-impact claims.")

    if scores.get("Transparency", 100) < 60:
        actions.append("Clarify which statements are verified facts and which are interpretation or inference.")

    if indicators.get("named_sources", 0) < 2:
        actions.append("Include more distinct named sources or clearly attributed source positions.")

    if indicators.get("loaded_words", 0) >= 2:
        actions.append("Tone down loaded phrasing and replace it with more neutral wording.")

    consistency_label, _ = headline_body_consistency(article_text)
    if consistency_label == "Weak":
        actions.append("Make the opening framing more proportional to the evidence shown in the article body.")

    if indicators.get("attributions", 0) < 2:
        actions.append("Add explicit attribution language to the most consequential claims.")

    if not actions:
        actions.append("No major mandatory action detected; proceed with final editorial review.")

    return actions[:4]


def final_editorial_verdict(scores: dict, indicators: dict, claims: list[str], article_text: str) -> dict:
    values = [v for v in scores.values() if isinstance(v, int)]
    avg = sum(values) / max(1, len(values))
    blocking = derive_blocking_issues(scores, indicators, claims, article_text)
    non_blocking = derive_non_blocking_issues(scores, indicators, article_text)
    actions = required_actions(scores, indicators, claims, article_text)

    if len(blocking) >= 3 or scores.get("Sourcing", 100) < 45 or scores.get("Transparency", 100) < 45:
        status = "Review manually"
        severity = "High"
    elif len(blocking) >= 1 or avg < 70:
        status = "Revise"
        severity = "Medium"
    else:
        status = "Publish"
        severity = "Low"

    if avg >= 78 and len(blocking) == 0:
        confidence = "High"
    elif avg >= 60:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "status": status,
        "severity": severity,
        "confidence": confidence,
        "blocking_issues": blocking,
        "non_blocking_issues": non_blocking,
        "required_actions": actions,
    }


# =============================================================================
# UTILS
# =============================================================================

def clean_claim_lines(raw_text: str) -> list[str]:
    claims = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        line = re.sub(r"^\d+[\).\-\s]+", "", line).strip()
        line = re.sub(r"^[-•]\s+", "", line).strip()

        if len(line) >= 12:
            claims.append(line)

    deduped = []
    seen = set()

    for claim in claims:
        key = claim.lower()
        if key not in seen:
            deduped.append(claim)
            seen.add(key)

    return deduped


def extract_numeric_score(line: str) -> Optional[int]:
    match = re.search(r":\s*(\d{1,3})\b", line)
    if not match:
        return None

    value = int(match.group(1))
    if 0 <= value <= 100:
        return value

    return None


def parse_scorecard(scorecard_text: str) -> dict:
    scores = {"Balance": None, "Sourcing": None, "Tone Neutrality": None, "Transparency": None}

    for line in scorecard_text.splitlines():
        line = line.strip()
        if not line:
            continue

        for key in scores.keys():
            if line.startswith(key):
                scores[key] = extract_numeric_score(line)

    return scores


def average_score(scores: dict) -> Optional[float]:
    values = [v for v in scores.values() if isinstance(v, int)]
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def quality_badge(avg: Optional[float]) -> str:
    if avg is None:
        return "Unknown"
    if avg >= 80:
        return "Strong"
    if avg >= 65:
        return "Moderate"
    if avg >= 45:
        return "Weak"
    return "High Risk"


def safe_preview(text: str, limit: int = 220) -> str:
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
        return "Medium risk"
    return "Low risk"


def score_color(score: int) -> str:
    if score >= 75:
        return "#2fbf71"
    if score >= 55:
        return "#f3a93b"
    return "#ef5a6f"


def verdict_css_class(status: str) -> str:
    if status == "Publish":
        return "publish"
    if status == "Revise":
        return "revise"
    return "review"


def verdict_display(status: str) -> str:
    if status == "Publish":
        return "Ready to publish"
    if status == "Revise":
        return "Revision required"
    return "Escalate for manual review"


def compact_reason(claim: str, claim_type: str, score: int) -> str:
    if claim_type in ["Predictive", "Interpretive", "Causal"]:
        return "This statement contains forward-looking or interpretive reasoning and should be qualified carefully."
    if claim_type == "Attributed allegation":
        return "This statement depends heavily on attribution quality and source clarity."
    if score >= 75:
        return "This is a high-impact claim and needs stronger evidential support before publication."
    if score >= 55:
        return "This claim is material enough to justify a closer sourcing review."
    return "This claim appears comparatively lower risk than the others."


def top_risk_claims(claims: list[str], article_text: str, indicators: dict, top_n: int = 6) -> list[dict]:
    rows = []

    for i, claim in enumerate(claims, 1):
        score = claim_risk_score(claim, article_text, indicators)
        rows.append({
            "index": i,
            "claim": claim,
            "score": score,
            "type": classify_claim_type(claim),
            "label": risk_label(score),
            "css": risk_css_class(score),
        })

    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[:top_n]


# =============================================================================
# ANALYSIS PIPELINES
# =============================================================================

def run_quick_analysis(client: OpenAI, article_text: str) -> dict:
    indicators = compute_indicators(article_text)
    indicator_scores = indicator_based_scores(indicators)
    raw_scorecard, llm_scores = press_scorecard(client, article_text)
    final_scores = merge_scores(llm_scores, indicator_scores, llm_weight=0.7)
    avg = average_score(final_scores)
    score_hint = decision_hint_from_scores(final_scores)
    claims = extract_claims(client, article_text)
    verdict = final_editorial_verdict(final_scores, indicators, claims, article_text)
    headline_label, headline_reason = headline_body_consistency(article_text)

    return {
        "mode": "quick",
        "indicators": indicators,
        "indicator_scores": indicator_scores,
        "raw_scorecard": raw_scorecard,
        "llm_scores": llm_scores,
        "final_scores": final_scores,
        "avg_score": avg,
        "quality_label": quality_badge(avg),
        "score_hint": score_hint,
        "claims": claims,
        "decision_text": None,
        "missing_text": None,
        "stakeholder_text": None,
        "verdict": verdict,
        "headline_label": headline_label,
        "headline_reason": headline_reason,
    }


def run_full_analysis(client: OpenAI, article_text: str) -> dict:
    base = run_quick_analysis(client, article_text)
    base["mode"] = "full"
    base["decision_text"] = editorial_decision(client, article_text)
    base["missing_text"] = analyze_missing_perspectives(client, article_text)
    base["stakeholder_text"] = stakeholder_review(client, article_text)
    return base


# =============================================================================
# SESSION STATE
# =============================================================================

def ensure_state():
    defaults = {
        "article_text": "",
        "article_url": "",
        "analysis_complete": False,
        "analysis_running": False,
        "analysis": None,
        "rewrite_text": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_api_key() -> Optional[str]:
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_header():
    st.markdown(
        """
        <div class="pa-hero">
            <div class="pa-kicker">AI-assisted newsroom review</div>
            <div class="pa-title">PressAnalyzer</div>
            <div class="pa-subtitle">
                Review an article before publication. The tool checks sourcing, balance,
                tone, transparency, and highlights the claims that most need verification.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_help_box():
    st.markdown(
        """
        <div class="pa-help">
            <strong>How to use it</strong><br>
            1. Paste article text or enter an article URL.<br>
            2. Choose <strong>Quick Review</strong> for a fast decision or <strong>Detailed Review</strong> for deeper analysis.<br>
            3. Run the audit and read the publication recommendation first.<br>
            4. Open the details only if you need evidence, claim review, or revision help.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_verdict_card(verdict: dict, quality_label: str, avg_score: Optional[float], score_hint: str,
                        headline_label: str, claim_count: int):
    css_class = verdict_css_class(verdict["status"])
    title = verdict_display(verdict["status"])

    st.markdown(
        f"""
        <div class="pa-verdict {css_class}">
            <div class="pa-verdict-label">Publication recommendation</div>
            <div class="pa-verdict-title">{title}</div>
            <div class="pa-verdict-text">{score_hint}</div>
            <div class="pa-chip-row">
                <div class="pa-chip">Severity: <strong>{verdict['severity']}</strong></div>
                <div class="pa-chip">Confidence: <strong>{verdict['confidence']}</strong></div>
                <div class="pa-chip">Quality: <strong>{quality_label}</strong></div>
                <div class="pa-chip">Average score: <strong>{avg_score if avg_score is not None else 'N/A'}</strong></div>
                <div class="pa-chip">Headline/body: <strong>{headline_label}</strong></div>
                <div class="pa-chip">Claims found: <strong>{claim_count}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_issue_panel(title: str, items: list[str]):
    items = items or ["No issues detected."]
    li_html = "".join(f"<li>{item}</li>" for item in items)

    st.markdown(
        f"""
        <div class="pa-card">
            <div class="pa-card-title">{title}</div>
            <ul class="pa-list">{li_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_card(final_scores: dict, headline_label: str, headline_reason: str):
    st.markdown('<div class="pa-card">', unsafe_allow_html=True)
    st.markdown('<div class="pa-card-title">Quality scores</div>', unsafe_allow_html=True)

    for label in ["Balance", "Sourcing", "Tone Neutrality", "Transparency"]:
        score = final_scores.get(label)
        if score is None:
            continue

        color = score_color(score)

        st.markdown(
            f"""
            <div class="pa-score-row">
                <div class="pa-score-label">{label}</div>
                <div class="pa-score-track">
                    <div class="pa-score-fill" style="width:{score}%; background:{color};"></div>
                </div>
                <div class="pa-score-num">{score}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="margin-top:0.9rem; padding-top:0.9rem; border-top:1px solid rgba(255,255,255,0.08);">
            <div class="pa-card-title" style="margin-bottom:0.35rem;">Headline / body consistency</div>
            <div style="font-weight:700; margin-bottom:0.3rem;">{headline_label}</div>
            <div class="pa-mini">{headline_reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)


def render_indicators_card(indicators: dict):
    mapping = [
        ("quotes", "Quotes"),
        ("attributions", "Attributions"),
        ("numbers", "Numbers"),
        ("loaded_words", "Loaded words"),
        ("hedges", "Hedges"),
        ("named_sources", "Named sources"),
        ("stakeholder_hints", "Stakeholder hints"),
    ]

    st.markdown('<div class="pa-card">', unsafe_allow_html=True)
    st.markdown('<div class="pa-card-title">Structural indicators</div>', unsafe_allow_html=True)

    for key, label in mapping:
        value = indicators.get(key, 0)
        concern = (
            (key == "named_sources" and value < 2) or
            (key == "attributions" and value < 2) or
            (key == "loaded_words" and value >= 3)
        )
        color = "#ef5a6f" if concern else "#edf2f7"

        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0.42rem 0; border-bottom:1px solid rgba(255,255,255,0.06);">
                <div class="pa-mini" style="font-size:0.92rem;">{label}</div>
                <div style="font-weight:800; color:{color};">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="margin-top:0.7rem;" class="pa-mini">
            Red values indicate potential editorial concerns.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


def render_claims(top_claims_rows: list[dict]):
    if not top_claims_rows:
        st.info("No claims were extracted from this article.")
        return

    for row in top_claims_rows:
        reason = compact_reason(row["claim"], row["type"], row["score"])
        st.markdown(
            f"""
            <div class="pa-claim {row['css']}">
                <div class="pa-claim-top">
                    <div class="pa-claim-type">Claim #{row['index']} · {row['type']}</div>
                    <div class="pa-badge {row['css']}">{row['label']} · {row['score']}/100</div>
                </div>
                <div style="font-size:0.96rem; line-height:1.55; margin-bottom:0.35rem;">{safe_preview(row['claim'])}</div>
                <div class="pa-mini">{reason}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================================
# APP
# =============================================================================

ensure_state()
render_header()
render_help_box()

with st.sidebar:
    st.markdown("### Configuration")
    secret_key = get_api_key()

    if secret_key:
        st.success("OpenAI key loaded from secrets")
        api_key = secret_key
    else:
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")

    st.divider()

    input_mode = st.radio(
        "Input type",
        ["Paste article text", "Article URL"],
        index=0,
    )

    review_mode = st.radio(
        "Review depth",
        ["Quick Review", "Detailed Review"],
        index=0,
    )

    st.divider()
    st.markdown("### Demo")
    if st.button("Load demo article", use_container_width=True):
        st.session_state["article_text"] = DEMO_ARTICLE
        st.session_state["analysis_complete"] = False
        st.session_state["analysis"] = None
        st.session_state["rewrite_text"] = None
        st.rerun()

    st.divider()
    st.markdown(
        """
        <div class="pa-mini">
            <strong>Quick Review</strong> = fast recommendation + core risks<br><br>
            <strong>Detailed Review</strong> = adds missing perspectives, editorial panel, and revision support
        </div>
        """,
        unsafe_allow_html=True,
    )

left, right = st.columns([2.2, 1], gap="large")

with left:
    st.markdown("### Article input")

    if input_mode == "Paste article text":
        article_text_input = st.text_area(
            "Article text",
            value=st.session_state.get("article_text", ""),
            height=300,
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
                with st.expander("Preview extracted article text"):
                    st.write(extracted[:3000])
            except Exception as e:
                st.error(f"Extraction failed: {e}")

    cta1, cta2 = st.columns(2)
    with cta1:
        run_clicked = st.button("Run editorial audit", use_container_width=True)
    with cta2:
        if st.button("Clear current article", use_container_width=True):
            st.session_state["article_text"] = ""
            st.session_state["article_url"] = ""
            st.session_state["analysis_complete"] = False
            st.session_state["analysis"] = None
            st.session_state["rewrite_text"] = None
            st.rerun()

with right:
    st.markdown("### What the tool checks")
    st.markdown(
        """
        <div class="pa-card">
            <div class="pa-card-title">Core review areas</div>
            <ul class="pa-list">
                <li><strong>Sourcing</strong> — are key claims properly attributed?</li>
                <li><strong>Balance</strong> — are relevant sides and stakeholders represented?</li>
                <li><strong>Tone</strong> — is the article neutral and proportionate?</li>
                <li><strong>Transparency</strong> — does the text separate fact, claim, and interpretation?</li>
                <li><strong>High-risk claims</strong> — which statements need stronger verification?</li>
                <li><strong>Missing perspectives</strong> — which voices, evidence, or context are absent?</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

article_text = st.session_state.get("article_text", "").strip()

if run_clicked:
    if not api_key:
        st.warning("Please enter an OpenAI API key.")
        st.stop()

    if len(article_text) < 250:
        st.warning("Article is too short. Please provide at least a few paragraphs.")
        st.stop()

    st.session_state["analysis_running"] = True
    st.session_state["analysis_complete"] = False
    st.session_state["analysis"] = None
    st.session_state["rewrite_text"] = None

    client = get_client(api_key)

    with st.status("Running editorial audit...", expanded=True) as status_box:
        st.write("Reading article structure...")
        st.write("Computing sourcing, balance, tone, and transparency...")
        st.write("Extracting the most important claims...")
        if review_mode == "Detailed Review":
            st.write("Running deeper editorial review...")
            result = run_full_analysis(client, article_text)
        else:
            result = run_quick_analysis(client, article_text)

        status_box.update(label="Analysis complete", state="complete")

    st.session_state["analysis"] = result
    st.session_state["analysis_running"] = False
    st.session_state["analysis_complete"] = True

if st.session_state.get("analysis_running"):
    st.info("Analysis is currently running...")

if st.session_state.get("analysis_complete") and st.session_state.get("analysis"):
    d = st.session_state["analysis"]

    indicators = d["indicators"]
    final_scores = d["final_scores"]
    avg_score = d["avg_score"]
    quality_label = d["quality_label"]
    score_hint = d["score_hint"]
    claims = d["claims"]
    decision_text = d["decision_text"]
    missing_text = d["missing_text"]
    stakeholder_text = d["stakeholder_text"]
    verdict = d["verdict"]
    headline_label = d["headline_label"]
    headline_reason = d["headline_reason"]
    raw_scorecard = d["raw_scorecard"]
    indicator_scores = d["indicator_scores"]

    risk_rows = top_risk_claims(claims, article_text, indicators, top_n=6)

    st.markdown("## Overview")

    render_verdict_card(
        verdict=verdict,
        quality_label=quality_label,
        avg_score=avg_score,
        score_hint=score_hint,
        headline_label=headline_label,
        claim_count=len(claims),
    )

    i1, i2, i3 = st.columns(3, gap="large")
    with i1:
        render_issue_panel("Critical issues", verdict["blocking_issues"])
    with i2:
        render_issue_panel("What to fix before publishing", verdict["required_actions"])
    with i3:
        render_issue_panel("Suggested improvements", verdict["non_blocking_issues"])

    st.markdown("## Core scores")

    s1, s2 = st.columns([1, 1], gap="large")
    with s1:
        render_score_card(final_scores, headline_label, headline_reason)
    with s2:
        render_indicators_card(indicators)

    st.markdown("## High-risk claims")
    render_claims(risk_rows)

    st.markdown("## Detailed review")

    if d["mode"] == "full":
        tabs = st.tabs([
            "Missing perspectives",
            "Editorial panel",
            "Claim-by-claim review",
            "Revision support",
            "Raw data",
        ])
    else:
        tabs = st.tabs([
            "Claim-by-claim review",
            "Revision support",
            "Raw data",
        ])

    if d["mode"] == "full":
        with tabs[0]:
            st.subheader("Missing voices, evidence, and context")
            st.write(missing_text or "No result available.")

        with tabs[1]:
            st.subheader("Simulated editorial review panel")
            st.write(stakeholder_text or "No result available.")

        claim_tab = tabs[2]
        rewrite_tab = tabs[3]
        raw_tab = tabs[4]
    else:
        claim_tab = tabs[0]
        rewrite_tab = tabs[1]
        raw_tab = tabs[2]

    with claim_tab:
        st.subheader("Claim-by-claim review")

        if not claims:
            st.info("No claims were extracted.")
        else:
            for i, claim in enumerate(claims, 1):
                ctype = classify_claim_type(claim)
                risk = claim_risk_score(claim, article_text, indicators)

                with st.expander(f"Claim {i} · {ctype} · {risk}/100"):
                    st.markdown(f"**Claim:** {claim}")
                    if st.button(f"Analyze claim {i}", key=f"claim_btn_{i}"):
                        with st.spinner("Analyzing claim..."):
                            result = analyze_claim(get_client(api_key), claim, article_text)
                        st.write(result)

    with rewrite_tab:
        st.subheader("Revision support")
        st.markdown("**Priority fixes**")
        for item in (verdict["required_actions"] or ["None."]):
            st.markdown(f"- {item}")

        st.divider()

        if st.button("Generate neutral rewrite"):
            with st.spinner("Generating rewrite..."):
                st.session_state["rewrite_text"] = rewrite_neutral(get_client(api_key), article_text)

        if st.session_state.get("rewrite_text"):
            st.markdown("**Neutral rewrite**")
            st.write(st.session_state["rewrite_text"])
        else:
            st.info("Click the button to generate a more neutral, publication-safe rewrite.")

    with raw_tab:
        st.subheader("Raw data and debug output")

        if decision_text:
            st.markdown("**Senior-editor decision**")
            st.write(decision_text)
            st.divider()

        st.markdown("**Raw scorecard**")
        st.code(raw_scorecard)

        st.markdown("**Indicator-based scores**")
        st.json(indicator_scores)

        st.markdown("**LLM scores**")
        st.json(d["llm_scores"])

        st.markdown("**Final merged scores**")
        st.json(final_scores)