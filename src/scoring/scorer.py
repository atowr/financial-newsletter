from datetime import datetime


VALID_TIERS = {"tier_1", "tier_2", "tier_3"}
VALID_CONTEXTUAL_SCORE = range(1, 6)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _parse_published_at(value):
    _require(value is not None, "published_at is required")

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise ValueError("published_at must be a datetime or ISO timestamp")

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("published_at must be a valid timestamp") from exc


def _normalise_tier(tier):
    if isinstance(tier, int) and tier in (1, 2, 3):
        return f"tier_{tier}"

    if isinstance(tier, str) and tier in VALID_TIERS:
        return tier

    raise ValueError("tier must be tier_1, tier_2, or tier_3")
def _get_tier_weight(article, config, tier):
    tier_weight = article.get("tier_weight")

    _require(
        tier_weight is not None,
        "tier_weight is required",
    )

    _require(
        isinstance(tier_weight, (int, float))
        and not isinstance(tier_weight, bool),
        "tier_weight must be numeric",
    )

    configured_weight = config.get("tiers", {}).get(tier, {}).get("weight")

    _require(
        configured_weight is not None,
        f"tier weight missing from config for {tier}",
    )

    _require(
        tier_weight == configured_weight,
        f"tier_weight does not match config for {tier}",
    )

    return configured_weight
def _validate_contract(article, config, run_timestamp):
    _require(
        article.get("validation_status") == "valid",
        "article must have validation_status='valid'",
    )

    tier = _normalise_tier(article.get("tier"))
    tier_weight = _get_tier_weight(article, config, tier)

    for field in (
        "adviser_relevance",
        "client_impact",
        "market_significance",
    ):
        value = article.get(field)

        _require(
            isinstance(value, int) and not isinstance(value, bool),
            f"{field} must be an integer",
        )

        _require(
            value in VALID_CONTEXTUAL_SCORE,
            f"{field} must be between 1 and 5",
        )
    _require(
        isinstance(run_timestamp, datetime),
        "run_timestamp must be a datetime",
    )

    published_at = _parse_published_at(article.get("published_at"))

    return tier, tier_weight, published_at
def calculate_article_score(article, config, run_timestamp):
    tier, tier_weight, published_at = _validate_contract(
        article,
        config,
        run_timestamp,
    )

    adviser_norm = (article["adviser_relevance"] - 1) * 25
    client_norm = (article["client_impact"] - 1) * 25
    market_norm = (article["market_significance"] - 1) * 25
    age_hours = (
        run_timestamp - published_at
    ).total_seconds() / 3600

    age_hours = max(0, age_hours)

    freshness_factor = max(
        0,
        1 - (age_hours / 24),
    )

    freshness_score = freshness_factor * 5
    final_score = (
        tier_weight * 0.40
        + adviser_norm * 0.15
        + client_norm * 0.25
        + market_norm * 0.15
        + freshness_score
    )

    final_score = min(100.0, final_score)

    return round(final_score, 1)
