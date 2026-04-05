import re


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

    sourcing = 30 + quotes * 4 + attributions * 5 + named_sources * 4 + min(numbers, 10) * 1.5
    balance = 35 + stakeholder_hints * 4 + min(named_sources, 8) * 2
    transparency = 30 + attributions * 4 + min(hedges, 8) * 3 + min(numbers, 10) * 1.2
    tone = 85 - loaded_words * 7 + min(hedges, 6) * 1.5

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
        return "Manual review is likely warranted because sourcing or transparency is weak."
    if avg < 60:
        return "Revision is likely needed before publication."
    if avg < 80:
        return "The article appears moderate in quality but may still need revision."
    return "The article appears comparatively strong on core quality dimensions."


def classify_claim_type(claim: str) -> str:
    text = claim.lower()

    if any(word in text for word in ["will", "could", "may", "might", "expected", "likely", "forecast"]):
        return "Predictive"
    if any(word in text for word in ["because", "due to", "led to", "caused", "resulted in"]):
        return "Causal"
    if any(word in text for word in ["according to", "said", "claimed", "reported", "alleged"]):
        return "Attributed allegation"
    if any(word in text for word in ["should", "unacceptable", "dangerous", "outrageous", "wrong"]):
        return "Evaluative"
    if any(word in text for word in ["suggests", "appears", "seems", "indicates", "signals"]):
        return "Interpretive"
    return "Factual"


def claim_risk_score(claim: str, article_text: str, indicators: dict) -> int:
    score = 35
    claim_lower = claim.lower()
    article_lower = article_text.lower()

    if classify_claim_type(claim) in ["Attributed allegation", "Interpretive", "Causal", "Predictive"]:
        score += 12

    if any(word in claim_lower for word in ["attack", "blame", "scandal", "fraud", "corrupt", "illegal"]):
        score += 12

    if not any(word in claim_lower for word in ["according to", "said", "reported", "stated", "announced"]):
        score += 8

    if any(word in claim_lower for word in ["will", "could", "may", "might", "appears", "seems", "suggests"]):
        score += 6

    if indicators.get("attributions", 0) < 2:
        score += 8

    if indicators.get("named_sources", 0) < 2:
        score += 8

    if indicators.get("loaded_words", 0) >= 3:
        score += 8

    if "response" not in article_lower and "statement" not in article_lower and "according to" not in article_lower:
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

    strong_words = ["attack", "shocking", "massive", "blasted", "furious", "dramatic", "explosive", "direct attack"]
    evidence_words = ["according to", "said", "reported", "statement", "data", "document", "confirmed", "announced"]

    strong_count = sum(1 for word in strong_words if word in headline_lower)
    evidence_count = sum(1 for word in evidence_words if word in body_lower)

    if strong_count >= 1 and evidence_count < 2:
        return "Weak", "The lead framing appears stronger than the supporting evidence signals in the body."
    if strong_count >= 1 and evidence_count >= 2:
        return "Moderate", "The framing is somewhat assertive, but the body includes at least some support."
    return "Strong", "The lead framing does not appear substantially stronger than the body support."


def derive_blocking_issues(scores: dict, indicators: dict, claims: list[str], article_text: str) -> list[str]:
    issues = []

    if scores.get("Sourcing", 100) < 45:
        issues.append("Central claims appear under-sourced for publication readiness.")

    if scores.get("Transparency", 100) < 45:
        issues.append("The article does not clearly distinguish what is verified, attributed, or inferred.")

    if indicators.get("named_sources", 0) < 2:
        issues.append("Too few distinct named sources are visible for a strong editorial release decision.")

    if indicators.get("attributions", 0) < 2:
        issues.append("The text lacks sufficient attribution for several claims.")

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
        issues.append("Some phrasing may sound more assertive or loaded than necessary.")

    if indicators.get("hedges", 0) == 0:
        issues.append("Uncertainty is not clearly signaled where interpretation may be involved.")

    if indicators.get("numbers", 0) == 0:
        issues.append("The article contains little visible quantitative support.")

    if "according to" not in article_text.lower() and "said" not in article_text.lower():
        issues.append("Attribution language could be made more explicit throughout the piece.")

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
        actions.append("Make the lead framing more proportional to the evidence shown in the article body.")

    if not actions:
        actions.append("No major mandatory action detected; proceed with final editorial review.")
    return actions[:4]


def final_editorial_verdict(scores: dict, indicators: dict, claims: list[str], article_text: str) -> dict:
    avg = sum(v for v in scores.values() if isinstance(v, int)) / max(
        1, len([v for v in scores.values() if isinstance(v, int)])
    )

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