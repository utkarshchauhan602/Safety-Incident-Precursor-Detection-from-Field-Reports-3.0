import json
from pathlib import Path

from spi.humanised_chat import CORPUS_PATH, corpus_size, get_humanised_example


def test_v3_corpus_has_exactly_fifty_thousand_jsonl_rows():
    assert corpus_size() == 50_000


def test_humanised_example_is_stable_and_matches_hazard():
    first = get_humanised_example("machine_guard", "guard was removed from conveyor")
    second = get_humanised_example("machine_guard", "guard was removed from conveyor")
    assert first == second
    assert first["hazard_key"] == "machine_guard"
    assert first["synthetic"] is True
    assert first["humanised_acknowledgement"]
    assert first["clarifying_question"]


def test_unknown_hazard_returns_no_example():
    assert get_humanised_example("unknown_hazard", "something happened") is None


def test_corpus_rows_are_valid_json_and_marked_synthetic():
    with CORPUS_PATH.open(encoding="utf-8") as handle:
        first = json.loads(next(handle))
        last = None
        for line in handle:
            last = json.loads(line)
    assert first["id"] == "HSE-00001"
    assert last["id"] == "HSE-50000"
    assert first["synthetic"] and last["synthetic"]
