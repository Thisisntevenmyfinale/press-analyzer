import re
from collections import Counter


ATTRIBUTION_PATTERNS = [
    r"\baccording to\b",
    r"\bsaid\b",
    r"\bstated\b",
    r"\breported\b",
    r"\breports\b",
    r"\bannounced\b",
    r"\bclaimed\b",
    r"\bclaims\b",
    r"\btold\b",
    r"\bdata from\b",
    r"\bfigures from\b",
    r"\bsource[d]?\b",
    r"\blaut\b",
    r"\bsagte\b",
    r"\berklärte\b",
    r"\bberichtete\b",
    r"\bzufolge\b",
]


HEDGE_PATTERNS = [
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\ballegedly\b",
    r"\breportedly\b",
    r"\bappears to\b",
    r"\bseems to\b",
    r"\bsuggests\b",
    r"\bkönnte\b",
    r"\bscheint\b",
    r"\boffenbar\b",
    r"\bmöglicherweise\b",
    r"\bsoll\b",
]


LOADED_WORDS = [
    "outrageous",
    "shocking",
    "devastating",
    "disastrous",
    "furious",
    "slam",
    "blasted",
    "explosive",
    "chaotic",
    "radical",
    "extreme",
    "massive",
    "dramatic",
    "dangerous",
    "scandal",
    "urknall",
    "hochgefährlich",
    "manisch",
    "panik",
    "machtdemonstration",
    "atemberaubend",
    "gnadenlos",
    "beben",
]


STAKEHOLDER_HINTS = [
    "government",
    "minister",
    "official",
    "company",
    "union",
    "workers",
    "residents",
    "citizens",
    "police",
    "court",
    "judge",
    "experts",
    "researchers",
    "activists",
    "critics",
    "supporters",
    "victims",
    "community",
    "spokesperson",
    "regierung",
    "ministerium",
    "unternehmen",
    "gewerkschaft",
    "arbeitnehmer",
    "bürger",
    "polizei",
    "gericht",
    "richter",
    "experten",
    "kritiker",
    "sprecher",
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
    curly = min(text.count("“"), text.count("”")) + min(text.count("„"), text.count("“"))
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

    fallback = re.findall(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b", text)
    for name in fallback:
        if name in COMMON_NON_SOURCE_WORDS:
            continue
        first = name.split()[0]
        if first in STOPWORD_TITLES:
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
    quotes = count_quotes(text)
    attributions = count_attributions(text)
    numbers = count_numbers(text)
    loaded_words = count_loaded_words(text)
    hedges = count_hedges(text)
    named_sources = count_distinct_named_sources(text)
    stakeholder_hints = count_stakeholder_hints(text)

    return {
        "quotes": quotes,
        "attributions": attributions,
        "numbers": numbers,
        "loaded_words": loaded_words,
        "hedges": hedges,
        "named_sources": named_sources,
        "stakeholder_hints": stakeholder_hints,
    }