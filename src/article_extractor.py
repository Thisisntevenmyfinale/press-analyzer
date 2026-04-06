import re
import requests
from bs4 import BeautifulSoup


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