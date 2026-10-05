import re
from difflib import SequenceMatcher


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()

def cluster_articles(articles: list[dict]) -> list[dict]:
    clusters = []
    for article in articles:
        matched = None
        for cluster in clusters:
            representative = cluster[0]
            title_similarity = _similarity(article.get("title", ""), representative.get("title", ""))
            summary_similarity = _similarity(article.get("summary", ""), representative.get("summary", ""))
            if title_similarity >= 0.80 and summary_similarity >= 0.70:
                matched = cluster
                break
        if matched is None:
            clusters.append([article])
        else:
            matched.append(article)
    for number, cluster in enumerate(clusters):
        canonical = max(
            cluster,
            key=lambda article: article.get("source_priority", 0),
        )
        for article in cluster:
            article["cluster_id"] = str(number)
            article["is_canonical"] = article is canonical
    return articles
