import re
import requests
from bs4 import BeautifulSoup


BAD_PHRASES = [
    # English
    "cookie",
    "cookies",
    "privacy policy",
    "privacy notice",
    "best experience on our website",
    "newsletter",
    "subscribe",
    "sign up",
    "log in",
    "accept",
    "consent",

    # German
    "datenschutz",
    "datenschutz-bestimmungen",
    "datenschutzbestimmungen",
    "abonnieren",
    "anmelden",
    "akzeptieren",
    "zustimmen",

    # Spanish
    "política de privacidad",
    "privacidad",
    "suscríbete",
    "suscribirse",
    "iniciar sesión",
    "regístrate",
    "aceptar",
    "consentimiento",
    "cookies para garantizar",
    "la mejor experiencia en nuestro sitio web",

    # French
    "politique de confidentialité",
    "confidentialité",
    "s’abonner",
    "abonnez-vous",
    "se connecter",
    "inscription",
    "accepter",
    "consentement",

    # Italian
    "informativa sulla privacy",
    "privacy",
    "abbonati",
    "iscriviti",
    "accedi",
    "registrati",
    "accetta",
    "consenso",

    # Portuguese
    "política de privacidade",
    "privacidade",
    "assine",
    "inscreva-se",
    "iniciar sessão",
    "entrar",
    "aceitar",
    "consentimento",
]


BAD_ATTR_KEYWORDS = [
    "cookie",
    "consent",
    "privacy",
    "gdpr",
    "newsletter",
    "subscribe",
    "signup",
    "sign-up",
    "login",
    "log-in",
    "paywall",
    "banner",
    "modal",
    "popup",
    "advert",
    "promo",
    "recommend",
    "recommended",
    "related",
    "share",
    "social",
    "menu",
    "search",
    "nav",
    "footer",
    "header",
]


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _is_date_or_timestamp(text: str) -> bool:
    patterns = [
        r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b\d{1,2}:\d{2}\b",
    ]
    return any(re.search(p, text) for p in patterns)


def _looks_like_junk(text: str) -> bool:
    lowered = text.lower().strip()

    if not lowered:
        return True

    if len(lowered) < 45:
        return True

    if _is_date_or_timestamp(lowered) and len(lowered) < 80:
        return True

    if any(phrase in lowered for phrase in BAD_PHRASES):
        return True

    junk_patterns = [
        r"^menu$",
        r"^menü$",
        r"^suche$",
        r"^search$",
        r"^buscar$",
        r"^home$",
        r"^weiterlesen$",
        r"^mehr lesen$",
        r"^read more$",
        r"^leer más$",
        r"^empfehlung der redaktion$",
        r"^recommended$",
        r"^related articles$",
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


def _remove_bad_nodes(soup: BeautifulSoup) -> None:
    for tag in soup([
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        "aside",
        "form",
        "button",
        "svg",
    ]):
        tag.decompose()

    for tag in soup.find_all(True):
        attrs = " ".join(
            [
                tag.get("id", "") or "",
                " ".join(tag.get("class", [])) if isinstance(tag.get("class", []), list) else "",
                tag.get("aria-label", "") or "",
                tag.get("role", "") or "",
            ]
        ).lower()

        if any(keyword in attrs for keyword in BAD_ATTR_KEYWORDS):
            tag.decompose()


def _extract_paragraphs(soup: BeautifulSoup) -> list[str]:
    paragraphs = []

    # 1. Bevorzugt article/main
    preferred_roots = []
    for selector in ["article", "main"]:
        preferred_roots.extend(soup.select(selector))

    roots = preferred_roots if preferred_roots else [soup]

    for root in roots:
        for p in root.find_all("p"):
            text = _normalize_whitespace(p.get_text(" ", strip=True))
            if _looks_like_junk(text):
                continue
            paragraphs.append(text)

    paragraphs = _deduplicate_paragraphs(paragraphs)

    # 2. Falls zu wenig extrahiert wurde, fallback: divs mit längeren Texten
    if len(" ".join(paragraphs).split()) < 180:
        extra = []
        for div in soup.find_all("div"):
            text = _normalize_whitespace(div.get_text(" ", strip=True))
            if len(text.split()) < 25:
                continue
            if _looks_like_junk(text):
                continue
            extra.append(text)

        paragraphs = _deduplicate_paragraphs(paragraphs + extra)

    return paragraphs


def extract_article_from_url(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    _remove_bad_nodes(soup)

    paragraphs = _extract_paragraphs(soup)
    article_text = "\n\n".join(paragraphs)

    if len(article_text.strip()) < 250:
        raise ValueError("No sufficiently clean article text could be extracted from this URL.")

    return article_text[:18000]