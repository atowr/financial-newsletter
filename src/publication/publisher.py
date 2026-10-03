from pathlib import Path

from src.rendering.renderer import render_newsletter


def publish_newsletter(newsletter, output_dir="docs"):
    """Render and persist the current newsletter and dated archive."""
    output_path = Path(output_dir)
    archive_path = output_path / "archive"

    output_path.mkdir(parents=True, exist_ok=True)
    archive_path.mkdir(parents=True, exist_ok=True)

    html = render_newsletter(newsletter)

    generated_date = newsletter["generated_at"][:10]
    dated_file = archive_path / f"{generated_date}.html"
    index_file = output_path / "index.html"

    dated_file.write_text(html, encoding="utf-8")
    index_file.write_text(html, encoding="utf-8")

    return {
        "index": str(index_file),
        "archive": str(dated_file),
    }
