CLAIM_EXTRACTION_PROMPT = """
You are an editorial intelligence assistant.

Task:
Extract the 5 to 8 most important claims from the article below.

Definition of a claim:
A claim is a concrete factual assertion, allegation, causal statement, statistic,
interpretive assertion, or evaluative statement that materially affects the article's message.

Rules:
- Keep each claim concise.
- Avoid duplicates.
- Do not include introductory text.
- Return only a numbered list.
- Claims should be understandable independently.

Article:
{article}
"""

CLAIM_ANALYSIS_PROMPT = """
You are evaluating a journalistic claim using newsroom-quality standards.

Analyze the following claim:

Claim:
{claim}

Article context:
{article}

Evaluate across:
- framing / bias risk
- evidence strength
- sourcing sufficiency
- emotional or loaded language
- missing perspective or counterpoint

Return your answer in exactly this format:

Bias Risk: <Low/Medium/High>
Evidence Strength: <Low/Medium/High>
Sourcing Sufficiency: <Low/Medium/High>
Emotional Language: <Yes/No>
Missing Perspective: <short phrase>
Editorial Note: <2-3 sentence explanation>
"""

MISSING_PERSPECTIVES_PROMPT = """
You are a senior editorial reviewer.

Read the article and identify what is missing from a press standards perspective.

Focus on:
- missing stakeholder voices
- missing evidence or data
- missing counterarguments
- missing historical or institutional context
- unclear attribution or transparency gaps

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

Why It Matters:
<2-4 sentences>

Suggested Newsroom Action:
<short recommendation>

Article:
{article}
"""

EDITORIAL_DECISION_PROMPT = """
You are a senior editor deciding whether an article is ready for publication.

Article:
{article}

Return your answer in exactly this structure:

Decision: <Publish / Revise / Review manually>

Reasoning:
- <bullet>
- <bullet>
- <bullet>

Confidence: <Low/Medium/High>
"""

REWRITE_NEUTRAL_PROMPT = """
Rewrite the following article to make it more neutral, balanced, and transparent.

Rules:
- preserve the core factual meaning as much as possible
- reduce emotionally loaded or sensational phrasing
- make uncertainty explicit where appropriate
- make attribution clearer
- do not invent facts
- do not add facts not present in the text

Article:
{article}
"""

STAKEHOLDER_REVIEW_PROMPT = """
You are simulating a newsroom review panel.

Article:
{article}

Provide evaluations from four perspectives:
1. Public editor
2. Fact-checker
3. Audience trust reviewer
4. Senior newsroom editor

For each perspective, return:
- Main concern
- Main strength
- Recommended action

Format:

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

Senior Newsroom Editor
Main concern: ...
Main strength: ...
Recommended action: ...
"""

PRESS_SCORECARD_PROMPT = """
You are scoring an article on newsroom quality dimensions.

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