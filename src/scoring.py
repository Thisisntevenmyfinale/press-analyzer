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