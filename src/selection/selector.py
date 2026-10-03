from datetime import datetime


SECTION_CATEGORY_MAP = {
    "Insurance & Insurers": {
        "insurance",
        "insurers",
    },
    "Funds & Asset Managers": {
        "fund_houses",
        "asset_managers",
    },
    "Financial Planning & Wealth": {
        "financial_planning",
        "wealth_management",
        "adviser_regulation",
        "mas_regulation",
    },
    "Singapore": {
        "singapore_economy",
        "singapore_markets",
    },
    "Asia & Global Markets": {
        "asia_markets",
        "monetary_policy",
        "major_earnings",
        "general_economy",
    },
    "Companies & Business": {
        "global_business",
    },
    "Rates, FX & Commodities": {
        "interest_rates",
        "bonds",
        "fx",
        "commodities",
    },
}


def _published_timestamp(article):
    value = article["published_at"]

    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _rank_key(article):
    return (
        -float(article["final_score"]),
        -int(article.get("source_priority", 0)),
        -_published_timestamp(article).timestamp(),
        article["id"],
    )


def rank_articles(articles):
    """Return eligible articles in deterministic descending priority order."""
    eligible = [
        article
        for article in articles
        if article.get("is_canonical") is True
        and article.get("category") != "unclassified"
        and article.get("final_score") is not None
    ]

    return sorted(eligible, key=_rank_key)


def section_for_category(category):
    """Return the deterministic publication section for a category."""
    for section_name, categories in SECTION_CATEGORY_MAP.items():
        if category in categories:
            return section_name

    return None


def select_top_stories(articles, max_count=5):
    """Select highest-ranked article from each distinct event cluster."""
    selected = []
    seen_clusters = set()

    for article in rank_articles(articles):
        cluster_id = article["cluster_id"]

        if cluster_id in seen_clusters:
            continue

        selected.append(article)
        seen_clusters.add(cluster_id)

        if len(selected) >= max_count:
            break

    return selected


def allocate_sections(articles, top_stories):
    """Allocate non-Top-Story articles to eligible sections."""
    top_ids = {article["id"] for article in top_stories}

    sections = {
        section_name: []
        for section_name in SECTION_CATEGORY_MAP
    }

    for article in rank_articles(articles):
        if article["id"] in top_ids:
            continue

        section_name = section_for_category(article["category"])

        if section_name is None:
            continue

        sections[section_name].append(article)

    return {
        name: section_articles
        for name, section_articles in sections.items()
        if section_articles
    }


def select_with_word_budget(
    articles,
    section_headers=None,
    market_snapshot=None,
    max_words=3000,
):
    """Remove lowest-priority stories until the reader-facing word budget passes."""
    selected = list(articles)

    while (
        selected
        and newsletter_word_count(
            selected,
            section_headers,
            market_snapshot,
        ) > max_words
    ):
        selected.pop()

    return selected


def validate_reading_time(word_count, max_words=3000, max_minutes=15):
    """Validate the hard newsletter word-count and reading-time limits."""
    reading_time = word_count / 200
    return (
        word_count <= max_words
        and reading_time <= max_minutes
    )


def publication_eligible(
    articles,
    section_headers=None,
    market_snapshot=None,
):
    """Return whether the final reader-facing newsletter passes Gate 10."""
    word_count = newsletter_word_count(
        articles,
        section_headers,
        market_snapshot,
    )

    return validate_reading_time(
        word_count,
        max_words=3000,
        max_minutes=15,
    )


def newsletter_word_count(
    articles,
    section_headers=None,
    market_snapshot=None,
):
    """Calculate the reader-facing newsletter word count."""
    total = 0

    for article in articles:
        for field in ("headline", "what_happened", "why_it_matters"):
            total += len(str(article.get(field, "")).split())

    for header in section_headers or []:
        total += len(str(header).split())

    for line in market_snapshot or []:
        total += len(str(line).split())

    return total

