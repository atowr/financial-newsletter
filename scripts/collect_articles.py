import yaml
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.collector.rss import collect_feed
from src.storage.sqlite import connect, insert_article

ROOT = Path(__file__).resolve().parents[1]

with open(ROOT / "config/sources.yaml") as f:
    config = yaml.safe_load(f)

db = connect(ROOT / "runtime/newsletter.db")

for source in config["sources"]:
    if source["enabled"]:
        articles = collect_feed(
            source["url"],
            source["id"],
            source["name"],
        )

        for article in articles:
            insert_article(db, article)

        print(source["name"], len(articles))

db.close()
