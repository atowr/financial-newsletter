Financial Adviser Newsletter: Scoring Rules

Version: 1.0 (LOCKED)
Status: APPROVED AND LOCKED
Effective: Gate 8 Implementation
Purpose: Define the exact mathematical formulas for deterministic story scoring (Gate 8 only)

APPROVED DECISIONS

All decisions in this document are locked.

Component	Value	Status
Tier weighting	40%	LOCKED
Adviser relevance	15%	LOCKED
Client impact	25%	LOCKED
Market significance	15%	LOCKED
Freshness	5%	LOCKED
Tier weights	100 / 70 / 40	LOCKED
Freshness decay	Linear over 24h	LOCKED
Future timestamp handling	Age < 0 → age = 0	LOCKED
Rounding	Final score only	LOCKED
TIER NORMALIZATION (LOCKED)

Tier weights are preserved as defined by the editorial hierarchy:

Tier 1: weight = 100
Tier 2: weight = 70
Tier 3: weight = 40

With a 40% tier contribution:

Tier 1 baseline = 100 × 0.40 = 40
Tier 2 baseline = 70 × 0.40 = 28
Tier 3 baseline = 40 × 0.40 = 16

Tier is not a ceiling.

A strong Tier 2 story can therefore outrank a weak Tier 1 story.

This is intentional and consistent with the Master Design.

RELEVANCE SCALE NORMALIZATION (LOCKED)

The following three AI-generated contextual scores use a 1–5 scale:

adviser_relevance
client_impact
market_significance

All are normalized to a common 0–100 scale using:

normalized_value = (raw_value - 1) × 25

Mapping:

Raw score	Normalized score
1	0
2	25
3	50
4	75
5	100

A raw score of 1 therefore contributes zero points from that dimension.

This is intentional.

FRESHNESS DECAY (LOCKED)

Freshness uses a deterministic linear decay over 24 hours.

Step 1: Calculate article age
age_hours = (
    run_timestamp - article.published_at
).total_seconds() / 3600
Step 2: Handle future timestamps

If the article timestamp is in the future:

if age_hours < 0:
    age_hours = 0

A future-dated article is therefore treated as having an age of zero hours.

Step 3: Calculate freshness factor
freshness_factor = max(0, 1 - (age_hours / 24))
Step 4: Calculate freshness contribution
freshness_score = freshness_factor * 5

Freshness therefore contributes between 0 and 5 points to the final score.

Freshness reference values
Article age	Freshness contribution
0h	5.00
6h	3.75
12h	2.50
18h	1.25
24h	0.00
48h	0.00
CRITICAL FRESHNESS IMPLEMENTATION NOTE

Freshness is represented directly as a 0–5 final contribution.

The 5% freshness weighting is therefore already embedded in the maximum contribution of 5 points.

Correct
freshness_score = freshness_factor * 5

This produces a contribution in the range:

0 ≤ freshness_score ≤ 5
Wrong — do not implement
freshness_score = freshness_factor * 5 * 0.05

That would double-apply the freshness weighting and reduce the maximum freshness contribution to 0.25 points.

The formula already accounts for the 5% limit through the five-point maximum contribution.

DETERMINISTIC RUN TIMESTAMP

The scoring run must use one fixed run_timestamp for all articles.

Capture the timestamp once at the beginning of the scoring run:

run_timestamp = datetime.utcnow()

or an equivalent timezone-aware implementation.

Then use that same timestamp for every article:

age_hours = (
    run_timestamp - article.published_at
).total_seconds() / 3600

Do not call the system clock separately for each article.

This ensures that all articles are scored against the same point in time and that the scoring result is deterministic for a given input set and run timestamp.

FINAL SCORE FORMULA (LOCKED)

The final score is:

final_score =
    tier_weight × 0.40
    + adviser_relevance_norm × 0.15
    + client_impact_norm × 0.25
    + market_significance_norm × 0.15
    + freshness_score

Where:

tier_weight ∈ {40, 70, 100}

adviser_relevance_norm ∈ [0, 100]

client_impact_norm ∈ [0, 100]

market_significance_norm ∈ [0, 100]

freshness_score ∈ [0, 5]

Therefore:

0 ≤ final_score ≤ 100
Important

The freshness contribution is already expressed as a 0–5 contribution.

Do not multiply freshness_score by 0.05 again.

ROUNDING (LOCKED)

All calculations must be performed at full precision.

Do not round intermediate values.

Only the final score is rounded:

final_score = round(final_score, 1)

Therefore:

intermediate calculations → full precision
final score               → 1 decimal place
WORKED EXAMPLES (LOCKED REFERENCE)
Example 1: Tier 1 Insurance Launch

Story:

"Great Eastern launches retirement insurance product"

Published: 2 hours ago

Inputs
tier_weight = 100

adviser_relevance = 5/5
→ adviser_relevance_norm = 100

client_impact = 5/5
→ client_impact_norm = 100

market_significance = 3/5
→ market_significance_norm = 50

age_hours = 2

Freshness:

freshness_factor = 1 - (2 / 24)
                  = 0.916666...

freshness_score = 0.916666... × 5
                = 4.583333...

Final calculation:

(100 × 0.40)
+ (100 × 0.15)
+ (100 × 0.25)
+ (50 × 0.15)
+ 4.583333...
= 40.0
+ 15.0
+ 25.0
+ 7.5
+ 4.583333...
= 92.083333...

Final score:

92.1
Example 2: Tier 2 Recession

Story:

"Singapore enters recession - GDP contracts 0.8%"

Published: 8 hours ago

Inputs
tier_weight = 70

adviser_relevance = 3/5
→ adviser_relevance_norm = 50

client_impact = 5/5
→ client_impact_norm = 100

market_significance = 5/5
→ market_significance_norm = 100

age_hours = 8

Freshness:

freshness_factor = 1 - (8 / 24)
                  = 0.666666...

freshness_score = 0.666666... × 5
                = 3.333333...

Final calculation:

(70 × 0.40)
+ (50 × 0.15)
+ (100 × 0.25)
+ (100 × 0.15)
+ 3.333333...
= 28.0
+ 7.5
+ 25.0
+ 15.0
+ 3.333333...
= 78.833333...

Final score:

78.8

Tier 2 baseline:

28 points

Strong contextual contribution:

50.833333... points

Total:

78.8

This exceeds a weak Tier 1 article whose contextual scores are all at their minimum:

40 + 0 + 0 + 0 + 0 = 40

This is correct behavior.

Example 3: Tier 3 Apple Product Launch

Story:

"Apple launches iPhone with AI features"

Published: 3 hours ago

Inputs
tier_weight = 40

adviser_relevance = 1/5
→ adviser_relevance_norm = 0

client_impact = 1/5
→ client_impact_norm = 0

market_significance = 2/5
→ market_significance_norm = 25

age_hours = 3

Freshness:

freshness_factor = 1 - (3 / 24)
                  = 0.875

freshness_score = 0.875 × 5
                = 4.375

Final calculation:

(40 × 0.40)
+ (0 × 0.15)
+ (0 × 0.25)
+ (25 × 0.15)
+ 4.375
= 16.0
+ 0
+ 0
+ 3.75
+ 4.375
= 24.125

Final score:

24.1
GATE 8 INPUT CONTRACT (LOCKED)

Gate 8 may score an article only if all required conditions are satisfied.

The article must have:

✓ validation_status = "valid"

✓ tier ∈ {1, 2, 3}

✓ tier_weight exists in configuration

✓ adviser_relevance ∈ {1, 2, 3, 4, 5}

✓ client_impact ∈ {1, 2, 3, 4, 5}

✓ market_significance ∈ {1, 2, 3, 4, 5}

✓ published_at exists and is a valid timestamp

✓ run_timestamp exists

If any required condition fails:

DO NOT SCORE

The article must instead be treated as a Gate 7 validation failure and skipped by Gate 8.

Gate 8 must not compensate for missing or invalid Gate 7 output.

GATE 8 SELF-CHECK VALIDATION (LOCKED)

Before scoring, the implementation must verify the scoring contract.

Weight validation
tier contribution        = 0.40
adviser relevance        = 0.15
client impact            = 0.25
market significance     = 0.15
freshness maximum        = 0.05

Total:

0.40 + 0.15 + 0.25 + 0.15 + 0.05 = 1.00

The freshness maximum of 0.05 corresponds to the five-point maximum contribution on a 0–100 final-score scale.

Input validation
assert tier in [1, 2, 3]
assert tier_weight in [40, 70, 100]

assert 1 <= adviser_relevance <= 5
assert 1 <= client_impact <= 5
assert 1 <= market_significance <= 5

assert 0 <= freshness_score <= 5
assert 0 <= final_score <= 100
Timestamp validation
assert run_timestamp is set once at start
assert all articles use the same run_timestamp
IMPLEMENTATION REFERENCE

The following is the reference implementation for Gate 8:

def calculate_article_score(
    article: ValidatedArticle,
    config: NewsletterConfig,
    run_timestamp: datetime
) -> float:
    """
    Gate 8: Calculate deterministic final score.

    Input:
        Article that passed Gate 7 validation.

    Output:
        Float score in the range [0, 100].

    Contract:
        See Gate 8 Input Contract.
    """

    # 1. Validate Gate 8 input contract
    assert_gate_8_contract(article, run_timestamp)

    # 2. Normalize contextual relevance scales
    adviser_norm = (article.adviser_relevance - 1) * 25
    client_norm = (article.client_impact - 1) * 25
    market_norm = (article.market_significance - 1) * 25

    # 3. Calculate freshness at full precision
    age_hours = (
        run_timestamp - article.published_at
    ).total_seconds() / 3600

    # Future timestamps are treated as age zero
    age_hours = max(0, age_hours)

    freshness_factor = max(
        0,
        1 - (age_hours / 24)
    )

    # Freshness is already the direct 0-5 contribution.
    freshness_score = freshness_factor * 5

    # 4. Combine all scoring components.
    # No intermediate rounding.
    final_score = (
        article.tier_weight * 0.40
        + adviser_norm * 0.15
        + client_norm * 0.25
        + market_norm * 0.15
        + freshness_score
    )

    # 5. Defensive upper bound
    final_score = min(100.0, final_score)

    # 6. Round final score only
    final_score = round(final_score, 1)

    return final_score
WHAT GATE 8 OWNS
Gate 8 owns
✓ Gate 8 input contract validation
✓ Deterministic score calculation
✓ Tier weighting
✓ Contextual score normalization
✓ Freshness calculation
✓ Final score calculation
✓ Final score rounding
✓ Scored article output
Gate 8 does NOT own
✗ Section allocation
✗ Cluster-aware selection
✗ Top Stories filtering
✗ Quality overrides
✗ Editorial overrides
✗ Word-count budgeting
✗ Reading-time selection
✗ Publication decisions

Those decisions belong to later gates, particularly Gate 9 where applicable.

Gate 8 must not introduce additional business rules that are not specified here.

GATE 8 OUTPUT

Gate 8 produces scored articles.

It does not own ranking or ordering.

Example:

[
  {
    "article_id": "canonical_article_1",
    "final_score": 92.1,
    "tier": 1,
    "category": "insurance",
    "cluster_id": "cluster_001"
  },
  {
    "article_id": "canonical_article_2",
    "final_score": 78.8,
    "tier": 2,
    "category": "singapore_economy",
    "cluster_id": "cluster_002"
  }
]

The output may contain the fields required by downstream processing, but Gate 8's scoring responsibility is specifically:

article → deterministic final_score

Gate 9 is responsible for ordering/ranking and selection decisions.

DETERMINISM REQUIREMENT

For identical:

article input
+
configuration
+
run_timestamp

Gate 8 must produce the identical final score.

There must be no:

✗ random weighting
✗ AI-generated score modification
✗ editorial override
✗ manual score adjustment
✗ per-article system-clock variation
✗ hidden scoring factor

The mathematical result must be reproducible and auditable.

GATE 8 TEST REQUIREMENTS

Before proceeding to Gate 9, Gate 8 must independently pass all of the following tests.

Test 1 — Worked examples

Verify the implementation produces:

Example 1 → 92.1
Example 2 → 78.8
Example 3 → 24.1
Test 2 — Freshness edge cases

Verify:

0h   → 5.00
6h   → 3.75
12h  → 2.50
18h  → 1.25
24h  → 0.00
48h  → 0.00

Also verify:

negative age → treated as 0h → freshness = 5.00
Test 3 — Input contract

Verify Gate 8 rejects/skips articles with:

invalid validation_status
invalid tier
missing tier_weight
adviser_relevance outside 1–5
client_impact outside 1–5
market_significance outside 1–5
missing published_at
invalid published_at
missing run_timestamp
Test 4 — Rounding

Verify that:

intermediate values remain full precision

and:

only final_score is rounded to 1 decimal place
Test 5 — Determinism

Given identical:

article
configuration
run_timestamp

the result must be identical across repeated executions.

Test 6 — Boundary validation

Verify:

minimum valid inputs
maximum valid inputs

produce a final score within:

0 ≤ final_score ≤ 100
VERSION HISTORY

Version 1.0 LOCKED

First authoritative and approved specification for Gate 8 deterministic scoring.

The following decisions are locked:

✓ 15% adviser relevance
✓ 25% client impact
✓ 15% market significance
✓ Linear 24-hour freshness decay
✓ Future timestamps treated as age zero
✓ Freshness represented as a direct 0–5 contribution
✓ Final-score-only rounding

