import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.classification.classifier import DeterministicClassifier
from src.collector.rss import collect_feed
from src.storage.sqlite import connect, insert_article
from src.processing.enrich_article import ArticleEnricher
from src.processing.cluster_articles import cluster_articles
from src.interpretation.validator import (
    validate_interpretation,
    FieldLengthError,
)
from src.interpretation.repair import repair_length_fields
from src.publication.publisher import publish_newsletter
from src.scoring.scorer import calculate_article_score
from src.selection.selector import (
    allocate_sections,
    newsletter_word_count,
    publication_eligible,
    select_top_stories,
    select_with_word_budget,
    rank_articles,
)
DB_PATH = ROOT / "runtime" / "newsletter.db"
SOURCES_CONFIG = ROOT / "config" / "sources.yaml"
CATEGORIES_CONFIG = ROOT / "config" / "categories.yaml"
OUTPUT_JSON = ROOT / "runtime" / "newsletter.json"


def load_articles():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            """
            SELECT
                id,
                source_id,
                source_name,
                title,
                url,
                published_at,
                summary
            FROM articles
            ORDER BY published_at DESC
            """
        ).fetchall()
    finally:
        conn.close()

    return [dict(row) for row in rows]


def deepseek_interpret(article):
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not set. "
            "The newsletter cannot truthfully be generated without "
            "the required DeepSeek interpretation stage."
        )

    base_url = os.environ.get(
        "DEEPSEEK_BASE_URL",
        "https://api.deepseek.com",
    ).rstrip("/")

    prompt = f"""
You are performing the editorial interpretation stage for the
Daily Financial Adviser Brief.

Use ONLY the supplied article information.

Article title:
{article["title"]}

Source:
{article["source_name"]}

Published at:
{article["published_at"]}

Article summary:
{article.get("summary") or ""}

Return ONLY valid JSON with exactly these fields:

{{
  "what_happened": "...",
  "why_it_matters": "...",
  "adviser_relevance": 1,
  "client_impact": 1,
  "market_significance": 1
}}

Requirements:

what_happened:
Write 25–40 words. Count the words yourself before returning the JSON.
Do not return the JSON until this field contains at least 25 words and no more than 40 words.
Keep it factual and source-grounded.

why_it_matters:
Write 20–30 words. Count the words yourself before returning the JSON.
Do not return the JSON until this field contains at least 20 words and no more than 30 words.
Keep it factual and relevant to financial advisers, clients or markets.

adviser_relevance:
integer 1–5.

client_impact:
integer 1–5.

market_significance:
integer 1–5.

Do not invent facts.
Do not speculate.
Do not make investment recommendations.
Do not predict.
Do not add fields.
"""

    payload = json.dumps(
        {
            "model": os.environ.get(
                "DEEPSEEK_MODEL",
                "deepseek-chat",
            ),
            "messages": [
                {
                    "role": "system",
                    "content": "Return JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0,
        }
    ).encode("utf-8")

    request = Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urlopen(request, timeout=120) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    content = result["choices"][0]["message"]["content"]

    for _ in range(3):
        try:
            return validate_interpretation(content)
        except FieldLengthError:
            repaired = json.loads(content)
            repaired = repair_length_fields(repaired, article)
            content = json.dumps(repaired)
        except ValueError as e:
            prompt += f"\nVALIDATION ERROR: {e}\nCorrect the field identified by the validation error. Return corrected JSON only."
            payload = json.dumps({
                "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
                "messages": [
                    {"role": "system", "content": "Return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0
            }).encode("utf-8")
            request = Request(
                f"{base_url}/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                method="POST"
            )
            with urlopen(request, timeout=120) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )
            content = result["choices"][0]["message"]["content"]

    return validate_interpretation(content)



def build_article(
    raw,
    classifier,
    enricher,
    config,
    run_timestamp,
):
    article = dict(raw)

    classification = classifier.classify(
        f'{article["title"]} '
        f'{article.get("summary") or ""}'
    )

    article.update(classification)

    article = enricher.enrich_source_priority(article)

    if article["category"] == "unclassified":
        return None

    article["cluster_id"] = str(article["id"])
    article["is_canonical"] = True

    interpretation = deepseek_interpret(article)

    article.update(interpretation)
    article["validation_status"] = "valid"

    article["final_score"] = calculate_article_score(
        article,
        config,
        run_timestamp,
    )

    return {
        "id": str(article["id"]),
        "source_id": article["source_id"],
        "source_name": article["source_name"],
        "source_priority": article["source_priority"],
        "title": article["title"],
        "url": article["url"],
        "published_at": article["published_at"],
        "summary": article.get("summary") or "",
        "category": article["category"],
        "tier": article["tier"],
        "cluster_id": article["cluster_id"],
        "is_canonical": article["is_canonical"],
        "what_happened": article["what_happened"],
        "why_it_matters": article["why_it_matters"],
        "adviser_relevance": article["adviser_relevance"],
        "client_impact": article["client_impact"],
        "market_significance": article["market_significance"],
        "final_score": article["final_score"],
    }


def main():
    run_timestamp = datetime.now(ZoneInfo("Asia/Singapore"))

    with open(
        CATEGORIES_CONFIG,
        "r",
        encoding="utf-8",
    ) as f:
        scoring_config = yaml.safe_load(f)

    classifier = DeterministicClassifier(
        CATEGORIES_CONFIG
    )

    enricher = ArticleEnricher(
        str(SOURCES_CONFIG)
    )

    with open(SOURCES_CONFIG, "r", encoding="utf-8") as f:
        source_config = yaml.safe_load(f)

    connection = connect(DB_PATH)
    collected = 0

    try:
        for source in source_config["sources"]:
            if not source.get("enabled", True):
                continue
            try:
                articles = collect_feed(
                    source["url"],
                    source["id"],
                    source["name"],
                )
            except Exception as exc:
                print(f"RSS feed failed: {source["name"]} — {exc}")
                continue
            for article in articles:
                insert_article(connection, article)
                collected += 1
    finally:
        connection.close()

    print(f"Collected RSS articles: {collected}")

    raw_articles = load_articles()

    enabled_source_ids = {
        source["id"]
        for source in source_config["sources"]
        if source.get("enabled", True)
    }
    raw_articles = [
        article
        for article in raw_articles
        if article["source_id"] in enabled_source_ids
    ]

    window_start = run_timestamp - timedelta(hours=26)

    raw_articles = [
        article
        for article in raw_articles
        if window_start
        <= datetime.fromisoformat(
            article["published_at"].replace("Z", "+00:00")
        ).astimezone(ZoneInfo("Asia/Singapore"))
        <= run_timestamp
    ]

    if not raw_articles:
        raise RuntimeError(
            "No articles found in newsletter.db"
        )

    articles = []

    for raw in raw_articles:
        article = build_article(
            raw,
            classifier,
            enricher,
            scoring_config,
            run_timestamp,
        )

        if article is not None:
            articles.append(article)

    articles = cluster_articles(articles)

    if not articles:
        raise RuntimeError(
            "No classified articles are eligible for publication"
        )

    top_stories = select_top_stories(
        articles,
        max_count=5,
        source_families=source_config.get("source_families", {}),
    )

    sections_map = allocate_sections(
        articles,
        top_stories,
    )

    sections = [
        {
            "name": name,
            "articles": section_articles,
        }
        for name, section_articles in sections_map.items()
    ]

    all_reader_articles = list(top_stories)

    for section in sections:
        all_reader_articles.extend(
            section["articles"]
        )

    all_reader_articles = select_with_word_budget(
        rank_articles(all_reader_articles),
        section_headers=[
            section["name"]
            for section in sections
        ],
        market_snapshot=None,
        max_words=3000,
    )

    selected_ids = {a["id"] for a in all_reader_articles}

    top_stories = [
        a for a in top_stories
        if a["id"] in selected_ids
    ]

    sections = [
        {
            "name": section["name"],
            "articles": [
                a for a in section["articles"]
                if a["id"] in selected_ids
            ],
        }
        for section in sections
    ]

    sections = [
        section for section in sections
        if section["articles"]
    ]

    section_headers = [
        section["name"]
        for section in sections
    ]

    word_count = newsletter_word_count(
        all_reader_articles,
        section_headers=section_headers,
        market_snapshot=None,
    )

    if not publication_eligible(
        all_reader_articles,
        section_headers=section_headers,
        market_snapshot=None,
    ):
        raise RuntimeError(
            "Publication eligibility FAILED: "
            f"word_count={word_count}"
        )

    newsletter = {
        "title": "Daily Financial Adviser Brief",
        "generated_at": run_timestamp.isoformat(),
        "target_reading_time_minutes": 12,
        "word_count": word_count,
        "reading_time_minutes": round(
            word_count / 200,
            2,
        ),
        "top_stories": top_stories,
        "sections": sections,
    }

    OUTPUT_JSON.write_text(
        json.dumps(
            newsletter,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    published = publish_newsletter(
        newsletter,
        output_dir=str(ROOT / "docs"),
    )

    print("PASS — newsletter object created")
    print(
        f"Newsletter object: {OUTPUT_JSON}"
    )
    print(f"Word count: {word_count}")
    print(
        "Reading time: "
        f"{newsletter['reading_time_minutes']} minutes"
    )
    print(
        f"Top stories: {len(top_stories)}"
    )
    print("Top story source families: " + ", ".join(source_config.get("source_families", {}).get(a.get("source_id"), a.get("source_id") or a.get("source_name")) for a in top_stories))
    print(
        f"Sections: {len(sections)}"
    )
    print(
        f"Published index: {published['index']}"
    )
    print(
        f"Published archive: {published['archive']}"
    )


if __name__ == "__main__":
    main()
