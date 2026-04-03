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


CONTENT_CLASS_HINTS = [
    "article",
    "content",
    "post",
    "story",
    "entry",
    "body",
    "main",
    "text",
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

    if len(lowered.split()) < 5:
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


def _safe_attr_string(tag) -> str:
    if not hasattr(tag, "attrs") or tag.attrs is None:
        return ""

    tag_id = tag.attrs.get("id", "") or ""
    tag_class = tag.attrs.get("class", []) or []
    aria_label = tag.attrs.get("aria-label", "") or ""
    role = tag.attrs.get("role", "") or ""

    if isinstance(tag_class, list):
        tag_class = " ".join(str(x) for x in tag_class)
    else:
        tag_class = str(tag_class)

    return f"{tag_id} {tag_class} {aria_label} {role}".lower().strip()


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
        try:
            tag.decompose()
        except Exception:
            pass

    tags_to_remove = []

    for tag in soup.find_all(True):
        attrs = _safe_attr_string(tag)
        if not attrs:
            continue

        if any(keyword in attrs for keyword in BAD_ATTR_KEYWORDS):
            tags_to_remove.append(tag)

    for tag in tags_to_remove:
        try:
            tag.decompose()
        except Exception:
            pass


def _collect_paragraphs_from_root(root) -> list[str]:
    paragraphs = []

    for p in root.find_all("p"):
        text = _normalize_whitespace(p.get_text(" ", strip=True))
        if _looks_like_junk(text):
            continue
        paragraphs.append(text)

    return paragraphs


def _candidate_content_divs(soup: BeautifulSoup):
    def class_matcher(value):
        if not value:
            return False

        if isinstance(value, list):
            joined = " ".join(str(v) for v in value).lower()
        else:
            joined = str(value).lower()

        return any(hint in joined for hint in CONTENT_CLASS_HINTS)

    return soup.find_all("div", class_=class_matcher)


def _extract_paragraphs(soup: BeautifulSoup) -> list[str]:
    paragraphs = []

    preferred_roots = []
    for selector in ["article", "main", "[role='main']"]:
        preferred_roots.extend(soup.select(selector))

    roots = preferred_roots if preferred_roots else [soup]

    for root in roots:
        paragraphs.extend(_collect_paragraphs_from_root(root))

    paragraphs = _deduplicate_paragraphs(paragraphs)

    if len(" ".join(paragraphs).split()) < 180:
        extra = []

        for div in _candidate_content_divs(soup):
            text = _normalize_whitespace(div.get_text(" ", strip=True))

            if len(text.split()) < 25:
                continue
            if _looks_like_junk(text):
                continue

            extra.append(text)

        paragraphs = _deduplicate_paragraphs(paragraphs + extra)

    return paragraphs


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


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

    response = requests.get(
        url,
        headers=headers,
        timeout=20,
        allow_redirects=True,
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise ValueError("URL did not return an HTML page.")

    soup = BeautifulSoup(response.text, "lxml")

    _remove_bad_nodes(soup)

    paragraphs = _extract_paragraphs(soup)
    article_text = "\n\n".join(paragraphs)

    if len(article_text.strip()) < 250:
        raise ValueError("No sufficiently clean article text could be extracted from this URL.")

    return article_text[:18000]