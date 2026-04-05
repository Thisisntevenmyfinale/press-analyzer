CLAIM_EXTRACTION_PROMPT = """
You are an editorial intelligence assistant for pre-publication newsroom review.

Task:
Extract the 5 to 8 most important claims from the article below.

Definition of a claim:
A claim is a concrete factual assertion, allegation, causal statement, statistic,
interpretive assertion, prediction, or evaluative statement that materially affects the article's message.

Rules:
- Keep each claim concise.
- Avoid duplicates.
- Do not include introductory text.
- Return only a numbered list.
- Claims should be understandable independently.
- Prioritize claims that matter most for editorial risk, verification, fairness, or publication readiness.

Article:
{article}
"""


CLAIM_ANALYSIS_PROMPT = """
You are evaluating a journalistic claim using newsroom-quality standards.

Analyze the following claim.

Claim:
{claim}

Article context:
{article}

Return your answer in exactly this structure:

Claim Type: <Factual / Attributed allegation / Interpretive / Causal / Predictive / Evaluative>
Verification Priority: <Low / Medium / High>
Bias Risk: <Low / Medium / High>
Evidence Strength: <Low / Medium / High>
Sourcing Sufficiency: <Low / Medium / High>
Certainty Inflation: <Yes / No>
Emotional Language: <Yes / No>
Missing Perspective: <short phrase>
Potential Harm Sensitivity: <Low / Medium / High>
Editorial Note: <2-4 sentences explaining why this claim is or is not risky for publication>
"""


MISSING_PERSPECTIVES_PROMPT = """
You are a senior editorial reviewer performing a pre-publication standards review.

Read the article and identify what is missing from a press standards perspective.

Focus on:
- missing stakeholder voices
- missing evidence or data
- missing counterarguments
- missing historical or institutional context
- unclear attribution or transparency gaps
- whether the criticized or affected side is missing

Return your answer in exactly this structure:

Missing Voices:
- <bullet>
- <bullet>

Missing Evidence:
- <bullet>
- <bullet>

Missing Context:
- <bullet>
- <bullet>

Transparency Gaps:
- <bullet>
- <bullet>

Most Important Omission:
<1-2 sentences>

Why It Matters:
<2-4 sentences>

Suggested Newsroom Action:
<short recommendation>

Article:
{article}
"""


EDITORIAL_DECISION_PROMPT = """
You are a senior editor deciding whether an article is ready for publication.

You are not just scoring quality. You are making a practical newsroom recommendation.

Article:
{article}

Return your answer in exactly this structure:

Decision: <Publish / Revise / Review manually>
Severity: <Low / Medium / High>

Blocking Issues:
- <bullet>
- <bullet>

Non-Blocking Issues:
- <bullet>
- <bullet>

Reasoning:
- <bullet>
- <bullet>
- <bullet>

Required Actions Before Publication:
- <bullet>
- <bullet>

Confidence: <Low / Medium / High>
"""


REWRITE_NEUTRAL_PROMPT = """
Rewrite the following article to make it more neutral, balanced, transparent, and publication-safe.

Rules:
- preserve the core factual meaning as much as possible
- reduce emotionally loaded or sensational phrasing
- make uncertainty explicit where appropriate
- make attribution clearer
- separate verified facts from interpretation where needed
- do not invent facts
- do not add facts not present in the text
- keep it readable and newsroom-appropriate

Article:
{article}
"""


STAKEHOLDER_REVIEW_PROMPT = """
You are simulating a newsroom review panel for a pre-publication editorial standards check.

Article:
{article}

Provide evaluations from these four perspectives:
1. Public Editor
2. Fact-Checker
3. Audience Trust Reviewer
4. Standards Editor

For each perspective, return:
- Main concern
- Main strength
- Recommended action

Then return a final section:

Panel Disagreement Level: <Low / Medium / High>
Escalation Recommendation: <Publish / Revise / Review manually>
Why: <2-3 sentences>

Format exactly as:

Public Editor
Main concern: ...
Main strength: ...
Recommended action: ...

Fact-Checker
Main concern: ...
Main strength: ...
Recommended action: ...

Audience Trust Reviewer
Main concern: ...
Main strength: ...
Recommended action: ...

Standards Editor
Main concern: ...
Main strength: ...
Recommended action: ...

Panel Disagreement Level: ...
Escalation Recommendation: ...
Why: ...
"""


PRESS_SCORECARD_PROMPT = """
You are scoring an article on newsroom quality dimensions for publication readiness.

Article:
{article}

Return scores from 0 to 100 for these dimensions:
- Balance
- Sourcing
- Tone Neutrality
- Transparency

Then provide one sentence per score.

Format exactly as:

Balance: <0-100> - <sentence>
Sourcing: <0-100> - <sentence>
Tone Neutrality: <0-100> - <sentence>
Transparency: <0-100> - <sentence>
"""