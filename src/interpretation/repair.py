import json
import os
from urllib.request import Request, urlopen
TARGETS = {
    "what_happened": 32,
    "why_it_matters": 25,
}

def repair_field(field, text, count, lo, hi, article):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set.")

    base_url = os.environ.get(
        "DEEPSEEK_BASE_URL",
        "https://api.deepseek.com",
    ).rstrip("/")
    target = TARGETS[field]

    direction = "shorten" if count > hi else "expand"

    prompt = f"""
Rewrite ONLY the field "{field}".

The existing text contains {count} words.
Permitted range: {lo}-{hi} words.
Target: exactly {target} words.
Action: {direction} the existing text.

Existing text:
{text}

Article title:
{article["title"]}

Article summary:
{article.get("summary") or ""}

Preserve the existing meaning.
Use only facts available in the existing text or supplied article information.
Do not invent facts.
Do not speculate, predict, or recommend.
Return ONLY the rewritten field text.
Do not return JSON.
"""

    payload = json.dumps({
        "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": "Return text only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }).encode("utf-8")

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
        result = json.loads(response.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"].strip()

def repair_length_fields(payload, article):
    from src.interpretation.validator import length_errors

    for error in length_errors(payload):
        for _ in range(3):
            text = repair_field(error.field, error.text, error.count, error.lo, error.hi, article)
            count = len(text.split())
            if error.lo <= count <= error.hi:
                payload[error.field] = text
                break
            error.text = text
            error.count = count
        else:
            payload[error.field] = text

    return payload
