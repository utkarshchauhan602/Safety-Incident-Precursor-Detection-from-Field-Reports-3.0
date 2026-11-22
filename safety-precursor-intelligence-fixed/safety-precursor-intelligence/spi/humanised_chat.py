"""Humanised response retrieval over the version 3.0 HSE conversation corpus.

The JSONL examples are synthetic phrasing/QA coverage, not real incident records,
clinical advice, safety procedures, or evidence of classifier performance.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

CORPUS_PATH = Path(__file__).parent / "data" / "humanised_hse_conversations.jsonl"
HAZARD_ORDER = (
    "electric_shock", "unconsciousness", "fire", "gas_release", "chemical_spill",
    "fall_height", "machine_guard", "slip_trip", "ppe", "vehicle",
)
ROWS_PER_HAZARD = 5_000


@lru_cache(maxsize=1)
def _line_offsets() -> tuple[int, ...]:
    """Index JSONL byte offsets once; keep memory use small and reads lazy."""
    offsets: list[int] = []
    with CORPUS_PATH.open("rb") as handle:
        while True:
            offset = handle.tell()
            line = handle.readline()
            if not line:
                break
            offsets.append(offset)
    return tuple(offsets)


def corpus_size() -> int:
    """Return the number of conversation examples in the bundled corpus."""
    return len(_line_offsets())


def get_humanised_example(hazard_key: str, user_text: str) -> dict[str, Any] | None:
    """Return a stable, varied empathy/clarification example for a hazard.

    Safety instructions still come exclusively from the curated playbook. This
    function supplies conversational phrasing only and never changes triage.
    """
    try:
        hazard_index = HAZARD_ORDER.index(hazard_key)
    except ValueError:
        return None
    offsets = _line_offsets()
    if len(offsets) < (hazard_index + 1) * ROWS_PER_HAZARD:
        return None
    digest = sha256(str(user_text).strip().lower().encode("utf-8")).digest()
    within_hazard = int.from_bytes(digest[:8], "big") % ROWS_PER_HAZARD
    row_index = hazard_index * ROWS_PER_HAZARD + within_hazard
    with CORPUS_PATH.open("rb") as handle:
        handle.seek(offsets[row_index])
        raw = handle.readline().decode("utf-8")
    try:
        record = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if record.get("hazard_key") != hazard_key:
        return None
    return record
