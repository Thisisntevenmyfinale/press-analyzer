import time
import re
from openai import OpenAI

from src.prompts import (
    CLAIM_EXTRACTION_PROMPT,
    CLAIM_ANALYSIS_PROMPT,
    MISSING_PERSPECTIVES_PROMPT,
    EDITORIAL_DECISION_PROMPT,
    REWRITE_NEUTRAL_PROMPT,
    STAKEHOLDER_REVIEW_PROMPT,
    PRESS_SCORECARD_PROMPT,
)
from src.utils import clean_claim_lines, parse_scorecard

DEFAULT_MODEL = "gpt-4o-mini"
STRONG_MODEL = "gpt-4o"


def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def run_prompt(
    client: OpenAI,
    prompt: str,
    temperature: float = 0.2,
    model: str = DEFAULT_MODEL,
    retries: int = 2,
) -> str:
    system = (
        "You are a precise editorial analysis assistant for newsroom-quality "
        "pre-publication review. Be structured, grounded, concise, and avoid hype."
    )
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                timeout=45,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
            else:
                raise RuntimeError(f"LLM call failed after {retries + 1} attempts: {e}") from e
    return ""


def extract_claims(client: OpenAI, article: str, model: str = DEFAULT_MODEL) -> list[str]:
    prompt = CLAIM_EXTRACTION_PROMPT.format(article=article[:12000])
    raw = run_prompt(client, prompt, temperature=0.1, model=model)
    return clean_claim_lines(raw)


def analyze_claim(client: OpenAI, claim: str, article: str, model: str = DEFAULT_MODEL) -> str:
    prompt = CLAIM_ANALYSIS_PROMPT.format(claim=claim, article=article[:9000])
    return run_prompt(client, prompt, temperature=0.1, model=model)


def analyze_missing_perspectives(client: OpenAI, article: str, model: str = DEFAULT_MODEL) -> str:
    prompt = MISSING_PERSPECTIVES_PROMPT.format(article=article[:10000])
    return run_prompt(client, prompt, temperature=0.2, model=model)


def editorial_decision(client: OpenAI, article: str, model: str = DEFAULT_MODEL) -> str:
    prompt = EDITORIAL_DECISION_PROMPT.format(article=article[:10000])
    return run_prompt(client, prompt, temperature=0.2, model=model)


def rewrite_neutral(client: OpenAI, article: str, model: str = DEFAULT_MODEL) -> str:
    prompt = REWRITE_NEUTRAL_PROMPT.format(article=article[:8000])
    return run_prompt(client, prompt, temperature=0.3, model=model)


def stakeholder_review(client: OpenAI, article: str, model: str = DEFAULT_MODEL) -> str:
    prompt = STAKEHOLDER_REVIEW_PROMPT.format(article=article[:10000])
    return run_prompt(client, prompt, temperature=0.25, model=model)


def press_scorecard(client: OpenAI, article: str, model: str = STRONG_MODEL) -> tuple[str, dict]:
    prompt = PRESS_SCORECARD_PROMPT.format(article=article[:10000])
    raw = run_prompt(client, prompt, temperature=0.1, model=model)
    parsed = parse_scorecard(raw)
    return raw, parsed
