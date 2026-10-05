import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.processing.cluster_articles import cluster_articles


def test_clusters_similar_articles():
    articles = [
        {
            "id": "st",
            "title": "Far East Orchard crosses $3 billion AUM target with higher stakes in business trust managers",
            "summary": "FEO is acquiring a 42% stake in Far East Hospitality Trust managers for $28.3 million.",
            "source_priority": 2,
        },
        {
            "id": "bt",
            "title": "Far East Orchard crosses S$3 billion AUM target with stake buys in business trust managers",
            "summary": "Far East Orchard is acquiring a 42% stake in Far East Hospitality Trust managers for S$28.3 million",
            "source_priority": 3,
        },
    ]
    result = cluster_articles(articles)
    assert result[0]["cluster_id"] == result[1]["cluster_id"]
    assert result[0]["is_canonical"] is False
    assert result[1]["is_canonical"] is True
