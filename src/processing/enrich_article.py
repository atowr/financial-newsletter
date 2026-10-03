import yaml
from typing import Any


class ArticleEnricher:
    """Deterministic article enrichment from configured source metadata."""

    def __init__(self, sources_config_path: str):
        with open(sources_config_path, "r") as f:
            config = yaml.safe_load(f)

        self.source_priority_map = {
            source["id"]: source["priority"]
            for source in config.get("sources", [])
            if source.get("id") and source.get("priority") is not None
        }

    def enrich_source_priority(self, article: dict[str, Any]) -> dict[str, Any]:
        source_id = article.get("source_id")

        if not source_id:
            raise ValueError("Article missing source_id")

        if source_id not in self.source_priority_map:
            raise ValueError(
                f"source_id '{source_id}' not found in configuration"
            )

        article["source_priority"] = self.source_priority_map[source_id]
        return article

    def enrich_batch(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.enrich_source_priority(article) for article in articles]
