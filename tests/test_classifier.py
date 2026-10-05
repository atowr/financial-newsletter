import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.classification.classifier import DeterministicClassifier


def test_aum_does_not_match_inside_trauma():
    classifier = DeterministicClassifier()

    result = classifier.classify(
        "The victims continued to bear emotional trauma from the deaths and injuries."
    )

    assert result["category"] == "unclassified"


def test_aum_matches_as_standalone_keyword():
    classifier = DeterministicClassifier()

    result = classifier.classify(
        "The company reported AUM of $3 billion."
    )

    assert result["category"] == "asset_managers"
