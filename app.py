import re
from collections import Counter
from typing import Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup
from openai import OpenAI


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="PressAnalyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_NAME = "gpt-4o-mini"

DEMO_ARTICLE = """
Die Gier ist zurück an der Wall Street, und sie trägt die Handschrift von Elon Musk und Sam Altman. Während die globale Geopolitik durch den Konflikt im Nahen Osten in den Grundfesten erschüttert wird, bereitet sich die US-Börse auf ein Spektakel vor, das alle bisherigen Dimensionen sprengen könnte. Die Zahlen des ersten Quartals 2026 sprechen eine deutliche Sprache: Das Emissionsvolumen bei Aktienverkäufen schoss um 40 Prozent auf atemberaubende 211 Milliarden Dollar nach oben. Es ist der stärkste Jahresauftakt seit dem Rekordjahr 2021 – ein finanzielles Hochamt inmitten des globalen Chaos.

Doch die eigentliche Prüfung steht erst noch bevor. Der Markt bereitet sich auf den „Urknall" vor: SpaceX steht kurz davor, an die Börse zu gehen. Mit einer angestrebten Bewertung von bis zu 1,75 Billionen Dollar und einem geplanten Emissionsvolumen von über 75 Milliarden Dollar wäre dies nicht nur ein Börsengang, sondern eine Machtdemonstration des Silicon Valley gegenüber der klassischen Industrie.

Hinter dem Weltraum-Giganten SpaceX drängt die nächste Welle der Disruption auf das Parkett. OpenAI und der Konkurrent Anthropic prüfen laut Insidern Listings, die ebenfalls zweistellige Milliardenbeträge in die Kassen spülen sollen. Diese KI-Infrastruktur-Titel erweisen sich als erstaunlich resistent gegenüber der allgemeinen Software-Schwäche.

„Die Widerstandsfähigkeit, die wir in diesem Markt angesichts all der Turbulenzen da draußen gesehen haben, ist ganz bemerkenswert", so John Kolz, Global Head of Equity Capital Markets bei Barclays.

Während in den USA die Tech-Träume die Kurse treiben, zeigt sich in Europa ein deutlich nüchterneres, aber ebenso lukratives Bild. Hier ist das IPO-Geschäft fest in der Hand der Rüstungsindustrie. Der tschechische Verteidigungskonzern CSG markierte mit einem 4,5-Milliarden-Dollar-Börsengang das bisherige Highlight des Quartals.
""".strip()


# =============================================================================
# STYLING
# =============================================================================

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #060a10;
  --panel: #0d131b;
  --panel2: #111925;
  --border: rgba(255,255,255,0.08);
  --border2: rgba(255,255,255,0.14);
  --text: #edf2f7;
  --muted: #9cabbe;
  --blue: #73a8ff;
}

html, body, .stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Inter', sans-serif !important;
}

.main .block-container {
  max-width: 1220px;
  padding-top: 1.2rem;
  padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0c1118 0%, #0a0f15 100%) !important;
  border-right: 1px solid var(--border2) !important;
}

h1, h2, h3, h4, h5, h6, p, span, div, label, li {
  color: var(--text) !important;
}

.stTextInput input, .stTextArea textarea {
  background: #101824 !important;
  color: var(--text) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 14px !important;
}

.stButton > button {
  background: var(--blue) !important;
  color: #06111d !important;
  border: none !important;
  border-radius: 14px !important;
  font-weight: 800 !important;
  padding: 0.72rem 1rem !important;
}

.stButton > button:hover {
  filter: brightness(1.04);
}

div[data-testid="stMetric"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 16px !important;
  padding: 1rem !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.5rem !important;
}

.stTabs [data-baseweb="tab"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 0.55rem 0.9rem !important;
}

.stTabs [aria-selected="true"] {
  border-color: var(--blue) !important;
}

.pa-hero {
  background: linear-gradient(180deg, #0d131c 0%, #091019 100%);
  border: 1px solid var(--border2);
  border-radius: 22px;
  padding: 1.3rem 1.4rem;
  margin-bottom: 1rem;
}

.pa-title {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 0.2rem;
}

.pa-sub {
  color: var(--muted) !important;
}

.pa-section {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: 1rem 0 0.7rem 0;
}

.pa-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1rem 1.05rem;
  height: 100%;
}

.pa-card-title {
  font-size: 0.78rem;
  color: var(--muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 800;
  margin-bottom: 0.7rem;
}

.pa-status-publish,
.pa-status-revise,
.pa-status-review {
  border-radius: 22px;
  padding: 1.2rem 1.25rem;
  border: 1px solid var(--border2);
  margin-bottom: 1rem;
}

.pa-status-publish {
  background: rgba(55,201,135,0.08);
  border-color: rgba(55,201,135,0.32);
}

.pa-status-revise {
  background: rgba(244,178,71,0.08);
  border-color: rgba(244,178,71,0.32);
}

.pa-status-review {
  background: rgba(239,98,120,0.08);
  border-color: rgba(239,98,120,0.32);
}

.pa-status-top {
  font-size: 0.78rem;
  color: var(--muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 700;
  margin-bottom: 0.35rem;
}

.pa-status-title {
  font-size: 1.9rem;
  font-weight: 800;
  line-height: 1.05;
  margin-bottom: 0.35rem;
}

.pa-status-text {
  color: var(--muted) !important;
  line-height: 1.5;
}

.pa-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.9rem;
}

.pa-chip {
  background: rgba(15,23,32,0.9);
  border: 1px solid var(--border2);
  border-radius: 999px;
  padding: 0.38rem 0.68rem;
  font-size: 0.8rem;
}

.pa-claim-box {
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 4px solid transparent;
  border-radius: 18px;
  padding: 1rem 1.05rem;
  margin-bottom: 0.85rem;
}

.pa-claim-high { border-left-color: #ef6278; }
.pa-claim-medium { border-left-color: #f4b247; }
.pa-claim-low { border-left-color: #37c987; }

.pa-claim-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.45rem;
}

.pa-claim-rank {
  color: var(--muted) !important;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 800;
}

.pa-claim-text {
  font-size: 1rem;
  line-height: 1.55;
  margin-bottom: 0.25rem;
}

.pa-claim-sub {
  color: var(--muted) !important;
  line-height: 1.45;
  font-size: 0.9rem;
}

.pa-badge-high,
.pa-badge-medium,
.pa-badge-low {
  border-radius: 999px;
  padding: 0.34rem 0.58rem;
  font-size: 0.76rem;
  font-weight: 800;
}

.pa-badge-high {
  color: #ef6278 !important;
  background: rgba(239,98,120,0.12);
  border: 1px solid rgba(239,98,120,0.28);
}

.pa-badge-medium {
  color: #f4b247 !important;
  background: rgba(244,178,71,0.12);
  border: 1px solid rgba(244,178,71,0.28);
}

.pa-badge-low {
  color: #37c987 !important;
  background: rgba(55,201,135,0.12);
  border: 1px solid rgba(55,201,135,0.28);
}

.pa-muted {
  color: var(--muted) !important;
}

div[data-testid="stProgressBar"] > div > div {
  border-radius: 999px !important;
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
        return "Not enough scoring information available."

    avg = sum(vals) / len(vals)
    sourcing = scores.get("Sourcing", 0)
    transparency = scores.get("Transparency", 0)

    if sourcing < 45 or transparency < 45:
        return "Sourcing or transparency is too weak for a confident release."
    if avg < 60:
        return "The article likely needs substantial revision."
    if avg < 80:
        return "The article is promising but still needs editorial tightening."
    return "The article performs well on the main publication-quality dimensions."


def classify_claim_type(claim: str) -> str:
    text = claim.lower()

    if any(w in text for w in ["will", "could", "may", "might", "expected", "likely", "forecast", "prüfen", "plant"]):
        return "Predictive"
    if any(w in text for w in ["because", "due to", "led to", "caused", "resulted in", "führt", "wegen", "verursacht"]):
        return "Causal"
    if any(w in text for w in ["according to", "said", "claimed", "reported", "alleged", "laut", "zufolge", "insidern"]):
        return "Attributed"
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

    if claim_type in ["Attributed", "Interpretive", "Causal", "Predictive", "Evaluative"]:
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
        return "Unknown", "No clear headline-like opener detected."

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
        return "Weak", "The opening framing appears stronger than the supporting evidence in the body."
    if strong_count >= 1 and evidence_count >= 2:
        return "Moderate", "The framing is assertive, but the body contains some evidence signals."
    return "Strong", "The opening framing looks proportionate to the article body."


def derive_blocking_issues(scores: dict, indicators: dict, claims: list[str], article_text: str) -> list[str]:
    issues = []

    if scores.get("Sourcing", 100) < 45:
        issues.append("Key claims appear under-sourced.")
    if scores.get("Transparency", 100) < 45:
        issues.append("Fact, attribution, and interpretation are not clearly separated.")
    if indicators.get("named_sources", 0) < 2:
        issues.append("Too few clearly named sources are visible.")
    if indicators.get("attributions", 0) < 2:
        issues.append("Several important claims are not clearly attributed.")

    high_risk_claims = sum(1 for claim in claims if claim_risk_score(claim, article_text, indicators) >= 75)
    if high_risk_claims >= 2:
        issues.append("Multiple claims carry elevated publication risk.")

    consistency_label, consistency_reason = headline_body_consistency(article_text)
    if consistency_label == "Weak":
        issues.append(f"Headline/body consistency is weak. {consistency_reason}")

    return issues[:4]


def derive_non_blocking_issues(scores: dict, indicators: dict, article_text: str) -> list[str]:
    issues = []

    if scores.get("Balance", 100) < 65:
        issues.append("The article may benefit from more stakeholder balance.")
    if scores.get("Tone Neutrality", 100) < 70:
        issues.append("Some language may be more loaded than necessary.")
    if indicators.get("hedges", 0) == 0:
        issues.append("Interpretation may not be clearly qualified.")
    if indicators.get("numbers", 0) == 0:
        issues.append("There is little visible quantitative support.")
    if ("according to" not in article_text.lower()
            and "said" not in article_text.lower()
            and "laut" not in article_text.lower()):
        issues.append("Attribution language could be more explicit.")

    return issues[:4]


def required_actions(scores: dict, indicators: dict, claims: list[str], article_text: str) -> list[str]:
    actions = []

    if scores.get("Sourcing", 100) < 60:
        actions.append("Add clearer sourcing to the highest-impact claims.")
    if scores.get("Transparency", 100) < 60:
        actions.append("Separate verified facts from interpretation more clearly.")
    if indicators.get("named_sources", 0) < 2:
        actions.append("Include more distinct named sources or clearly attributed positions.")
    if indicators.get("loaded_words", 0) >= 2:
        actions.append("Replace loaded phrasing with more neutral wording.")

    consistency_label, _ = headline_body_consistency(article_text)
    if consistency_label == "Weak":
        actions.append("Make the opening framing more proportional to the evidence in the body.")

    if indicators.get("attributions", 0) < 2:
        actions.append("Add explicit attribution to the most consequential claims.")

    if not actions:
        actions.append("No major mandatory actions detected.")

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


def quality_label(avg: Optional[float]) -> str:
    if avg is None:
        return "Unknown"
    if avg >= 80:
        return "Strong"
    if avg >= 65:
        return "Moderate"
    if avg >= 45:
        return "Weak"
    return "High risk"


def score_color(score: int) -> str:
    if score >= 75:
        return "🟢"
    if score >= 55:
        return "🟠"
    return "🔴"


def verdict_class_name(status: str) -> str:
    if status == "Publish":
        return "pa-status-publish"
    if status == "Revise":
        return "pa-status-revise"
    return "pa-status-review"


def verdict_title(status: str) -> str:
    if status == "Publish":
        return "Ready to publish"
    if status == "Revise":
        return "Revision required"
    return "Manual review needed"


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


def safe_preview(text: str, limit: int = 260) -> str:
    text = " ".join(text.split())
    return text[:limit].rstrip() + "…" if len(text) > limit else text


def compact_reason(claim_type: str, score: int) -> str:
    if claim_type in ["Predictive", "Interpretive", "Causal"]:
        return "This statement depends on interpretation or forward-looking reasoning."
    if claim_type == "Attributed":
        return "This statement depends heavily on source clarity and attribution quality."
    if score >= 75:
        return "This is one of the most sensitive statements in the article."
    if score >= 55:
        return "This statement deserves an extra sourcing check."
    return "This statement appears lower risk than the others."


def build_ranked_claims(claims: list[str], article_text: str, indicators: dict, top_n: int = 6) -> list[dict]:
    rows = []
    for claim in claims:
        score = claim_risk_score(claim, article_text, indicators)
        rows.append({
            "claim": claim,
            "score": score,
            "type": classify_claim_type(claim),
            "css": risk_css_class(score),
            "label": risk_label(score),
        })

    rows.sort(key=lambda x: x["score"], reverse=True)

    ranked = []
    for i, row in enumerate(rows[:top_n], 1):
        ranked.append({
            "rank": i,
            **row,
        })
    return ranked


def build_all_claim_rows(claims: list[str], article_text: str, indicators: dict) -> list[dict]:
    rows = []
    for i, claim in enumerate(claims, 1):
        score = claim_risk_score(claim, article_text, indicators)
        rows.append({
            "index": i,
            "claim": claim,
            "score": score,
            "type": classify_claim_type(claim),
        })
    return rows


def signal_state(value: int, good_if_at_least: Optional[int] = None, bad_if_more_than: Optional[int] = None) -> str:
    if good_if_at_least is not None and value >= good_if_at_least:
        return "good"
    if bad_if_more_than is not None and value > bad_if_more_than:
        return "bad"
    return "warn"


# =============================================================================
# ANALYSIS
# =============================================================================

def run_quick_analysis(client: OpenAI, article_text: str) -> dict:
    indicators = compute_indicators(article_text)
    indicator_scores = indicator_based_scores(indicators)
    raw_scorecard, llm_scores = press_scorecard(client, article_text)
    final_scores = merge_scores(llm_scores, indicator_scores, llm_weight=0.7)
    avg = average_score(final_scores)
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
        "quality_label": quality_label(avg),
        "score_hint": decision_hint_from_scores(final_scores),
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
# STATE
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
# RENDER HELPERS
# =============================================================================

def render_header():
    st.markdown(
        """
        <div class="pa-hero">
          <div class="pa-title">PressAnalyzer</div>
          <div class="pa-sub">Pre-publication editorial review</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status(verdict: dict, quality: str, avg_score: Optional[float], hint: str,
                  headline_label: str, claim_count: int):
    css_class = verdict_class_name(verdict["status"])
    html = f"""
    <div class="{css_class}">
      <div class="pa-status-top">Publication recommendation</div>
      <div class="pa-status-title">{verdict_title(verdict['status'])}</div>
      <div class="pa-status-text">{hint}</div>
      <div class="pa-chip-row">
        <div class="pa-chip">Severity: {verdict['severity']}</div>
        <div class="pa-chip">Confidence: {verdict['confidence']}</div>
        <div class="pa-chip">Quality: {quality}</div>
        <div class="pa-chip">Score: {avg_score if avg_score is not None else 'N/A'}</div>
        <div class="pa-chip">Headline/body: {headline_label}</div>
        <div class="pa-chip">Claims: {claim_count}</div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_issue_box(title: str, items: list[str]):
    if not items:
        items = ["No issues detected."]
    li_html = "".join(f"<li>{item}</li>" for item in items)
    st.markdown(
        f"""
        <div class="pa-card">
          <div class="pa-card-title">{title}</div>
          <ul>{li_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scores_native(final_scores: dict, headline_label: str, headline_reason: str):
    with st.container(border=True):
        st.markdown("##### Quality scores")

        for label in ["Balance", "Sourcing", "Tone Neutrality", "Transparency"]:
            score = final_scores.get(label)
            if score is None:
                continue

            c1, c2, c3 = st.columns([1.5, 4, 0.8])
            with c1:
                st.markdown(f"**{label}**")
            with c2:
                st.progress(int(score))
            with c3:
                st.markdown(f"**{score}**")

        st.divider()
        st.markdown(f"**Headline/body consistency:** {headline_label}")
        st.caption(headline_reason)


def evidence_signal_rows(indicators: dict) -> list[dict]:
    return [
        {
            "name": "Direct quotes",
            "value": indicators.get("quotes", 0),
            "desc": "Quoted statements inside the article",
            "icon": "🟢" if indicators.get("quotes", 0) >= 2 else "🟠",
        },
        {
            "name": "Attribution signals",
            "value": indicators.get("attributions", 0),
            "desc": 'Phrases like "according to", "said", or "reported"',
            "icon": "🟢" if indicators.get("attributions", 0) >= 2 else "🔴",
        },
        {
            "name": "Numbers and figures",
            "value": indicators.get("numbers", 0),
            "desc": "Visible statistics, counts, percentages, or amounts",
            "icon": "🟢" if indicators.get("numbers", 0) >= 1 else "🟠",
        },
        {
            "name": "Loaded words",
            "value": indicators.get("loaded_words", 0),
            "desc": "Emotionally charged or sensational wording",
            "icon": "🟢" if indicators.get("loaded_words", 0) == 0 else ("🟠" if indicators.get("loaded_words", 0) < 3 else "🔴"),
        },
        {
            "name": "Uncertainty markers",
            "value": indicators.get("hedges", 0),
            "desc": 'Qualifiers like "may", "could", or "appears"',
            "icon": "🟢" if indicators.get("hedges", 0) >= 1 else "🟠",
        },
        {
            "name": "Named sources",
            "value": indicators.get("named_sources", 0),
            "desc": "Distinct named people clearly used as sources",
            "icon": "🟢" if indicators.get("named_sources", 0) >= 2 else "🔴",
        },
        {
            "name": "Stakeholder coverage",
            "value": indicators.get("stakeholder_hints", 0),
            "desc": "Signals that different sides or affected groups are mentioned",
            "icon": "🟢" if indicators.get("stakeholder_hints", 0) >= 2 else "🟠",
        },
    ]


def render_signals_native(indicators: dict):
    with st.container(border=True):
        st.markdown("##### Evidence signals")
        rows = evidence_signal_rows(indicators)

        for row in rows:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{row['name']}**")
                st.caption(row["desc"])
            with c2:
                st.markdown(f"### {row['icon']} {row['value']}")


def render_ranked_claims(ranked_claims: list[dict]):
    if not ranked_claims:
        st.info("No claims extracted.")
        return

    for row in ranked_claims:
        badge_class = {
            "high": "pa-badge-high",
            "medium": "pa-badge-medium",
            "low": "pa-badge-low",
        }[row["css"]]

        box_class = {
            "high": "pa-claim-box pa-claim-high",
            "medium": "pa-claim-box pa-claim-medium",
            "low": "pa-claim-box pa-claim-low",
        }[row["css"]]

        st.markdown(
            f"""
            <div class="{box_class}">
              <div class="pa-claim-top">
                <div class="pa-claim-rank">Risk #{row['rank']} · {row['type']}</div>
                <div class="{badge_class}">{row['label']} · {row['score']}/100</div>
              </div>
              <div class="pa-claim-text">{safe_preview(row['claim'])}</div>
              <div class="pa-claim-sub">{compact_reason(row['type'], row['score'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================================
# APP
# =============================================================================

ensure_state()
render_header()

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

left, right = st.columns([2.1, 1], gap="large")

with left:
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
                with st.expander("Preview extracted text"):
                    st.write(extracted[:3000])
            except Exception as e:
                st.error(f"Extraction failed: {e}")

    c1, c2 = st.columns(2)
    with c1:
        run_clicked = st.button("Run audit", use_container_width=True)
    with c2:
        if st.button("Clear", use_container_width=True):
            st.session_state["article_text"] = ""
            st.session_state["article_url"] = ""
            st.session_state["analysis_complete"] = False
            st.session_state["analysis"] = None
            st.session_state["rewrite_text"] = None
            st.rerun()

with right:
    st.metric("Mode", review_mode)
    st.metric("Input", input_mode)
    st.metric("Article length", len(st.session_state.get("article_text", "").split()))

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
        st.write("Reading article...")
        st.write("Scoring sourcing, balance, tone, and transparency...")
        st.write("Extracting key claims...")

        if review_mode == "Detailed Review":
            st.write("Running deeper review...")
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
    verdict = d["verdict"]
    headline_label = d["headline_label"]
    headline_reason = d["headline_reason"]
    claims = d["claims"]
    ranked_claims = build_ranked_claims(claims, article_text, indicators, top_n=6)
    all_claim_rows = build_all_claim_rows(claims, article_text, indicators)

    st.markdown('<div class="pa-section">Overview</div>', unsafe_allow_html=True)
    render_status(
        verdict=verdict,
        quality=d["quality_label"],
        avg_score=avg_score,
        hint=d["score_hint"],
        headline_label=headline_label,
        claim_count=len(claims),
    )

    o1, o2, o3 = st.columns(3, gap="large")
    with o1:
        render_issue_box("Critical issues", verdict["blocking_issues"])
    with o2:
        render_issue_box("Fix before publishing", verdict["required_actions"])
    with o3:
        render_issue_box("Secondary improvements", verdict["non_blocking_issues"])

    st.markdown('<div class="pa-section">Core scores</div>', unsafe_allow_html=True)
    s1, s2 = st.columns(2, gap="large")
    with s1:
        render_scores_native(final_scores, headline_label, headline_reason)
    with s2:
        render_signals_native(indicators)

    st.markdown('<div class="pa-section">Highest-risk claims</div>', unsafe_allow_html=True)
    render_ranked_claims(ranked_claims)

    if d["mode"] == "full":
        tabs = st.tabs(["Claims", "Missing perspectives", "Panel", "Rewrite", "Raw"])
    else:
        tabs = st.tabs(["Claims", "Rewrite", "Raw"])

    if d["mode"] == "full":
        claim_tab = tabs[0]
        missing_tab = tabs[1]
        panel_tab = tabs[2]
        rewrite_tab = tabs[3]
        raw_tab = tabs[4]
    else:
        claim_tab = tabs[0]
        rewrite_tab = tabs[1]
        raw_tab = tabs[2]

    with claim_tab:
        st.subheader("All extracted claims")
        for row in all_claim_rows:
            with st.expander(f"Claim {row['index']} · {row['type']} · {row['score']}/100"):
                st.markdown(f"**Claim:** {row['claim']}")
                if st.button(f"Analyze claim {row['index']}", key=f"analyze_claim_{row['index']}"):
                    with st.spinner("Analyzing claim..."):
                        claim_result = analyze_claim(get_client(api_key), row["claim"], article_text)
                    st.write(claim_result)

    if d["mode"] == "full":
        with missing_tab:
            st.subheader("Missing perspectives")
            st.write(d["missing_text"] or "No result available.")

        with panel_tab:
            st.subheader("Editorial panel")
            st.write(d["stakeholder_text"] or "No result available.")

    with rewrite_tab:
        st.subheader("Rewrite support")
        for item in verdict["required_actions"] or ["No required actions detected."]:
            st.markdown(f"- {item}")

        st.divider()

        if st.button("Generate neutral rewrite"):
            with st.spinner("Generating rewrite..."):
                st.session_state["rewrite_text"] = rewrite_neutral(get_client(api_key), article_text)

        if st.session_state.get("rewrite_text"):
            st.write(st.session_state["rewrite_text"])

    with raw_tab:
        st.subheader("Raw outputs")
        if d["decision_text"]:
            st.markdown("**Senior-editor decision**")
            st.write(d["decision_text"])
            st.divider()

        st.markdown("**Raw scorecard**")
        st.code(d["raw_scorecard"])

        st.markdown("**Indicator-based scores**")
        st.json(d["indicator_scores"])

        st.markdown("**LLM scores**")
        st.json(d["llm_scores"])

        st.markdown("**Final merged scores**")
        st.json(d["final_scores"])