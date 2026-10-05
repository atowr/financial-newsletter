from pathlib import Path
import re
import yaml


class DeterministicClassifier:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = (
                Path(__file__).resolve().parents[2]
                / "config"
                / "categories.yaml"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.tiers = self.config["tiers"]
        self.rules = self.config["classification"]["categories"]

        self.category_to_tier = {}
        self.tier_weights = {}
        
        for tier_name, tier_config in self.tiers.items():
            self.tier_weights[tier_name] = tier_config["weight"]
            for category in tier_config["categories"]:
                self.category_to_tier[category] = tier_name

    @staticmethod
    def _normalise(text):
        return re.sub(r"\s+", " ", text.lower()).strip()

    def classify(self, text):
        text = self._normalise(text)
        matches = []

        for category, rule in self.rules.items():
            excluded = any(
                exclusion.lower() in text
                for exclusion in rule.get("exclusions", [])
            )

            if excluded:
                continue

            matched = any(
                phrase.lower() in text
                for phrase in rule.get("phrases", [])
            ) or any(
                re.search(r"\b" + re.escape(keyword.lower()) + r"\b", text)
                for keyword in rule.get("keywords", [])
            )

            if matched:
                matches.append((rule["priority"], category))

        if not matches:
            return {
                "category": "unclassified",
                "tier": None,
                "tier_weight": None,
            }

        _, category = max(matches)
        tier = self.category_to_tier[category]

        return {
            "category": category,
            "tier": tier,
            "tier_weight": self.tier_weights[tier],
        }
