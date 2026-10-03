import json


REQUIRED_FIELDS = {
    "what_happened",
    "why_it_matters",
    "adviser_relevance",
    "client_impact",
    "market_significance",
}
LENGTH_LIMITS = {"what_happened": (25, 40), "why_it_matters": (20, 30)}
def word_count(text):
    return len(text.split())



class FieldLengthError(ValueError):
    def __init__(self, field, count, lo, hi, text):
        self.field, self.count, self.lo, self.hi, self.text = field, count, lo, hi, text
        super().__init__(f"{field} must be between {lo} and {hi} words")

def validate_interpretation(payload):
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("AI output is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("AI output must be a JSON object")

    if set(payload.keys()) != REQUIRED_FIELDS:
        raise ValueError("AI output contains missing or unexpected fields")

    for field in ("what_happened", "why_it_matters"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ValueError(f"{field} must be a non-empty string")

        lo, hi = LENGTH_LIMITS[field]
        count = word_count(payload[field])

        if not lo <= count <= hi:
            raise FieldLengthError(field, count, lo, hi, payload[field])

    for field in (
        "adviser_relevance",
        "client_impact",
        "market_significance",
    ):
        value = payload[field]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field} must be an integer")
        if not 1 <= value <= 5:
            raise ValueError(f"{field} must be between 1 and 5")

    return payload

def length_errors(payload):
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return []

    if not isinstance(payload, dict):
        return []

    errors = []
    for field, (lo, hi) in LENGTH_LIMITS.items():
        text = payload.get(field)
        if isinstance(text, str) and text.strip():
            count = word_count(text)
            if not lo <= count <= hi:
                errors.append(FieldLengthError(field, count, lo, hi, text))
    return errors
