import re


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


def extract_numeric_score(line: str) -> int | None:
    match = re.search(r":\s*(\d{1,3})\b", line)
    if not match:
        return None

    value = int(match.group(1))
    if 0 <= value <= 100:
        return value
    return None


def parse_scorecard(scorecard_text: str) -> dict:
    scores = {
        "Balance": None,
        "Sourcing": None,
        "Tone Neutrality": None,
        "Transparency": None,
    }

    for line in scorecard_text.splitlines():
        line = line.strip()
        if not line:
            continue

        for key in scores.keys():
            if line.startswith(key):
                scores[key] = extract_numeric_score(line)

    return scores


def average_score(scores: dict) -> float | None:
    values = [v for v in scores.values() if isinstance(v, int)]
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def risk_badge_label(avg: float | None) -> str:
    if avg is None:
        return "Unknown"
    if avg >= 80:
        return "Strong"
    if avg >= 65:
        return "Moderate"
    if avg >= 45:
        return "Weak"
    return "High Risk"