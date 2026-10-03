import pytest

from src.processing.enrich_article import ArticleEnricher


def test_enrich_source_priority_valid():
    enricher = ArticleEnricher("config/sources.yaml")

    article = {
        "source_id": "cna_business",
        "title": "Singapore banks report profits",
    }

    enriched = enricher.enrich_source_priority(article)

    assert enriched["source_priority"] == 90
    assert enriched["source_id"] == "cna_business"
    assert enriched["title"] == "Singapore banks report profits"


def test_enrich_source_priority_invalid_source():
    enricher = ArticleEnricher("config/sources.yaml")

    article = {
        "source_id": "unknown_source",
        "title": "Some story",
    }

    with pytest.raises(ValueError):
        enricher.enrich_source_priority(article)


def test_enrich_source_priority_missing_source_id():
    enricher = ArticleEnricher("config/sources.yaml")

    article = {
        "title": "Some story",
    }

    with pytest.raises(ValueError):
        enricher.enrich_source_priority(article)
