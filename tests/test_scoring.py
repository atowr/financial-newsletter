from datetime import datetime, timezone

import pytest

from src.scoring.scorer import calculate_article_score

CONFIG = {
    "tiers": {
        "tier_1": {"weight": 100},
        "tier_2": {"weight": 70},
        "tier_3": {"weight": 40},
    }
}

RUN_TIMESTAMP = datetime(2026, 9, 29, 6, 0, tzinfo=timezone.utc)


def valid_article():
    return {
        "validation_status": "valid",
        "tier": 1,
        "tier_weight": 100,
        "adviser_relevance": 5,
        "client_impact": 5,
        "market_significance": 3,
        "published_at": "2026-09-29T04:00:00+00:00",
    }

def test_worked_examples():
    article = valid_article()
    assert calculate_article_score(article, CONFIG, RUN_TIMESTAMP) == 92.1

    article.update({
        "tier": 2,
        "tier_weight": 70,
        "adviser_relevance": 3,
        "client_impact": 5,
        "market_significance": 5,
        "published_at": "2026-09-28T22:00:00+00:00",
    })
    assert calculate_article_score(article, CONFIG, RUN_TIMESTAMP) == 78.8

    article.update({
        "tier": 3,
        "tier_weight": 40,
        "adviser_relevance": 1,
        "client_impact": 1,
        "market_significance": 2,
        "published_at": "2026-09-29T03:00:00+00:00",
    })
    assert calculate_article_score(article, CONFIG, RUN_TIMESTAMP) == 24.1

@pytest.mark.parametrize(
    "hours, expected",
    [
        (0, 45.0),
        (6, 43.8),
        (12, 42.5),
        (18, 41.2),
        (24, 40.0),
        (48, 40.0),
        (-6, 45.0),
    ],
)
def test_freshness(hours, expected):
    article = valid_article()
    article.update({
        "adviser_relevance": 1,
        "client_impact": 1,
        "market_significance": 1,
    })
    published = RUN_TIMESTAMP.timestamp() - hours * 3600
    article["published_at"] = datetime.fromtimestamp(
        published, tz=timezone.utc
    ).isoformat()

    assert calculate_article_score(
        article, CONFIG, RUN_TIMESTAMP
    ) == expected

@pytest.mark.parametrize(
    "changes, message",
    [
        ({"validation_status": "invalid"}, "validation_status"),
        ({"tier": 4}, "tier"),
        ({"tier_weight": None}, "tier_weight is required"),
        ({"tier_weight": 70}, "does not match config"),
        ({"adviser_relevance": 0}, "adviser_relevance"),
        ({"client_impact": 6}, "client_impact"),
        ({"market_significance": 0}, "market_significance"),
        ({"published_at": None}, "published_at is required"),
        ({"published_at": "not-a-date"}, "valid timestamp"),
    ],
)
def test_invalid_input_contract(changes, message):
    article = valid_article()
    article.update(changes)

    with pytest.raises(ValueError, match=message):
        calculate_article_score(
            article, CONFIG, RUN_TIMESTAMP
        )


def test_invalid_run_timestamp():
    article = valid_article()

    with pytest.raises(ValueError, match="run_timestamp"):
        calculate_article_score(
            article, CONFIG, "2026-09-29T06:00:00+00:00"
        )

def test_full_precision_final_rounding():
    article = valid_article()
    article.update({
        "tier": 2,
        "tier_weight": 70,
        "adviser_relevance": 2,
        "client_impact": 3,
        "market_significance": 4,
        "published_at": "2026-09-29T04:30:00+00:00",
    })

    assert calculate_article_score(
        article, CONFIG, RUN_TIMESTAMP
    ) == 60.2

def test_deterministic_score():
    article = valid_article()

    first = calculate_article_score(
        article, CONFIG, RUN_TIMESTAMP
    )
    second = calculate_article_score(
        article, CONFIG, RUN_TIMESTAMP
    )

    assert first == second == 92.1

def test_minimum_boundary():
    article = valid_article()
    article.update({
        "tier": 3,
        "tier_weight": 40,
        "adviser_relevance": 1,
        "client_impact": 1,
        "market_significance": 1,
        "published_at": "2026-09-28T06:00:00+00:00",
    })

    assert calculate_article_score(
        article, CONFIG, RUN_TIMESTAMP
    ) == 16.0

def test_maximum_boundary():
    article = valid_article()
    article["market_significance"] = 5
    article["published_at"] = "2026-09-29T06:00:00+00:00"

    assert calculate_article_score(
        article, CONFIG, RUN_TIMESTAMP
    ) == 100.0
