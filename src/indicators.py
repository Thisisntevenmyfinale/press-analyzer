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
]


def count_quotes(text: str) -> int:
    double_quotes = text.count('"') // 2
    curly_quotes = min(text.count("“"), text.count("”"))
    return double_quotes + curly_quotes


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
    candidates = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", text)
    cleaned = []
    blacklist = {
        "The", "A", "An", "This", "That", "These", "Those",
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday", "January", "February", "March", "April",
        "May", "June", "July", "August", "September", "October",
        "November", "December"
    }
    for c in candidates:
        first = c.split()[0]
        if first not in blacklist and len(c) > 2:
            cleaned.append(c)
    return cleaned


def count_distinct_named_sources(text: str) -> int:
    candidates = extract_named_source_candidates(text)
    counts = Counter(candidates)
    distinct = [k for k, v in counts.items() if v >= 1]
    return len(distinct)


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