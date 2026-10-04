import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.selection.selector import newsletter_word_count

def test_newsletter_word_count():
    a = [{"headline":"Market rises","what_happened":"Stocks gained today","why_it_matters":"Clients may benefit","source_name":"Excluded Source","url":"https://x.com"}]
    assert newsletter_word_count(a, ["Top Stories"], ["STI +0.42%"]) == 12

def test_select_top_stories_prefers_source_family_diversity():
    from src.selection.selector import select_top_stories

    articles = [
        {
            "id": "bloomberg-1",
            "final_score": 100,
            "source_priority": 90,
            "published_at": "2026-10-04T08:00:00+00:00",
            "cluster_id": "c1",
            "source_id": "bloomberg_markets",
            "source_name": "Bloomberg Markets",
            "category": "general_economy",
            "is_canonical": True,
            "adviser_relevance": 2,
            "client_impact": 1,
            "market_significance": 1,
        },
        {
            "id": "bloomberg-2",
            "final_score": 99,
            "source_priority": 90,
            "published_at": "2026-10-04T07:59:00+00:00",
            "cluster_id": "c2",
            "source_id": "bloomberg_business",
            "source_name": "Bloomberg Business",
            "category": "global_business",
            "is_canonical": True,
            "adviser_relevance": 2,
            "client_impact": 1,
            "market_significance": 1,
        },
        {
            "id": "cna-1",
            "final_score": 98,
            "source_priority": 90,
            "published_at": "2026-10-04T07:58:00+00:00",
            "cluster_id": "c3",
            "source_id": "cna_business",
            "source_name": "CNA Business",
            "category": "global_business",
            "is_canonical": True,
            "adviser_relevance": 2,
            "client_impact": 1,
            "market_significance": 1,
        },
        {
            "id": "bt-1",
            "final_score": 97,
            "source_priority": 90,
            "published_at": "2026-10-04T07:57:00+00:00",
            "cluster_id": "c4",
            "source_id": "bt_companies_markets",
            "source_name": "Business Times - Companies & Markets",
            "category": "global_business",
            "is_canonical": True,
            "adviser_relevance": 2,
            "client_impact": 1,
            "market_significance": 1,
        },
    ]

    families = {
        "bloomberg_markets": "Bloomberg",
        "bloomberg_business": "Bloomberg",
        "cna_business": "CNA",
        "bt_companies_markets": "Business Times",
    }

    selected = select_top_stories(
        articles,
        max_count=3,
        source_families=families,
    )

    assert [article["id"] for article in selected] == [
        "bloomberg-1",
        "cna-1",
        "bt-1",
    ]

def test_disabled_source_is_excluded_from_selection():
    from src.selection.selector import select_top_stories

    articles = [
        {
            "id": "disabled-bloomberg",
            "final_score": 100,
            "source_priority": 90,
            "published_at": "2026-10-04T08:00:00+00:00",
            "cluster_id": "c1",
            "source_id": "bloomberg_markets",
            "source_name": "Bloomberg Markets",
            "category": "general_economy",
            "is_canonical": True,
            "adviser_relevance": 2,
            "client_impact": 1,
            "market_significance": 1,
        },
        {
            "id": "enabled-cna",
            "final_score": 90,
            "source_priority": 90,
            "published_at": "2026-10-04T07:59:00+00:00",
            "cluster_id": "c2",
            "source_id": "cna_business",
            "source_name": "CNA Business",
            "category": "global_business",
            "is_canonical": True,
            "adviser_relevance": 2,
            "client_impact": 1,
            "market_significance": 1,
        },
    ]

    enabled_source_ids = {"cna_business"}

    eligible = [
        article
        for article in articles
        if article["source_id"] in enabled_source_ids
    ]

    selected = select_top_stories(eligible, max_count=5)

    assert [article["id"] for article in selected] == ["enabled-cna"]

def test_relevance_eligibility_excludes_zero_signal_article():
    from src.selection.selector import is_relevance_eligible, rank_articles

    irrelevant = {
        "id": "irrelevant",
        "final_score": 19.5,
        "source_priority": 90,
        "published_at": "2026-10-04T08:00:00+00:00",
        "cluster_id": "c1",
        "category": "commodities",
        "is_canonical": True,
        "adviser_relevance": 1,
        "client_impact": 1,
        "market_significance": 1,
    }

    relevant = {
        **irrelevant,
        "id": "relevant",
        "final_score": 50.0,
        "cluster_id": "c2",
        "adviser_relevance": 2,
    }

    assert is_relevance_eligible(irrelevant) is False
    assert is_relevance_eligible(relevant) is True
    assert [a["id"] for a in rank_articles([irrelevant, relevant])] == ["relevant"]
