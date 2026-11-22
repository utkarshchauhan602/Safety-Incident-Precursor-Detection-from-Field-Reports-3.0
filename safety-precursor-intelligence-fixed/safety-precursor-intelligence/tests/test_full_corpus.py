"""Exhaustive regression suite for all contextual utterances."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spi.scenario_corpus import SCENARIO_CORPUS
from spi.triage import detect_hazard

def test_all_9000_contextual_examples_match_expected_label():
    mismatches = []
    for expected, phrase in SCENARIO_CORPUS:
        result = detect_hazard(phrase)
        actual = result.key if result else None
        if actual != expected:
            mismatches.append((expected, actual, phrase))
    assert not mismatches, mismatches[:20]
