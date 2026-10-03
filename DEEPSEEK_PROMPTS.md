# DeepSeek AI Interpretation Contract

## Purpose

DeepSeek is used only for editorial interpretation of an already classified, canonical article.

Python and configuration remain authoritative for:

- category
- tier
- source priority
- publication date
- freshness
- duplicate detection
- article clustering
- canonical article selection
- section eligibility
- final score
- ranking
- section allocation
- publication eligibility

DeepSeek must not make or override these decisions.

## Required Output

DeepSeek must return valid JSON containing exactly:

{
  "what_happened": "...",
  "why_it_matters": "...",
  "adviser_relevance": 4,
  "client_impact": 4,
  "market_significance": 3
}

No additional fields are permitted.

## Field Requirements

### what_happened

A factual summary of what happened.

- source-grounded
- factual
- approximately 25–40 words
- no speculation
- no unsupported inference
- no investment recommendation
- no prediction presented as fact

### why_it_matters

Explain why the reported development is relevant to financial advisers, their clients, or financial markets.

- source-supported
- factual
- approximately 20–30 words
- no speculation
- no unsupported inference
- no investment recommendation
- no prediction
- do not tell advisers what they should recommend or do

### adviser_relevance

Integer from 1 to 5.

### client_impact

Integer from 1 to 5.

### market_significance

Integer from 1 to 5.

## Editorial Rules

DeepSeek must:

1. Use only information supported by the supplied article material.
2. Distinguish reported facts from interpretation.
3. Avoid inventing facts, figures, motives, causes, or consequences.
4. Avoid predictions.
5. Avoid investment advice.
6. Avoid product recommendations.
7. Avoid buy, sell, hold, or allocation instructions.
8. Avoid telling advisers what they should recommend to clients.
9. Avoid changing the deterministic category or tier.
10. Return JSON only.

If the article does not contain enough evidence to explain an implication, state the relevance conservatively rather than inventing one.

## Output Discipline

Return only the JSON object.

Do not return:

- Markdown
- code fences
- commentary
- explanations
- confidence statements
- additional fields

## Gate 6 Contract

Gate 6 passes only when DeepSeek produces valid output satisfying:

- required fields present
- no unexpected fields
- adviser_relevance is an integer 1–5
- client_impact is an integer 1–5
- market_significance is an integer 1–5
- what_happened is non-empty
- why_it_matters is non-empty
- output is valid JSON

Invalid AI output must not silently proceed to later stages.
