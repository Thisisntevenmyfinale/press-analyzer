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


MODEL_NAME = "gpt-4o-mini"


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
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def extract_claims(client: OpenAI, article: str) -> list[str]:
    prompt = CLAIM_EXTRACTION_PROMPT.format(article=article[:12000])
    raw = run_prompt(client, prompt, temperature=0.1)
    return clean_claim_lines(raw)


def analyze_claim(client: OpenAI, claim: str, article: str) -> str:
    prompt = CLAIM_ANALYSIS_PROMPT.format(
        claim=claim,
        article=article[:9000],
    )
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