"""Text normalization and robust phrase matching utilities."""
from __future__ import annotations
import re
import unicodedata
from functools import lru_cache
from difflib import SequenceMatcher

COMMON_REPLACEMENTS = {
    "shocked": "electric shock", "got shock": "electric shock",
    "current hit": "electric shock", "current passed": "electric shock",
    "slept": "sleeping", "fell asleep": "sleeping", "dozed": "sleeping",
    "nodding off": "sleeping", "electrocuted": "electric shock",
    "wire is sparking": "sparking electrical wire",
    "smoke coming": "smoke detected", "gas smell": "possible gas release",
    "not wearing helmet": "helmet missing", "no helmet": "helmet missing",
    "almost hit": "near miss collision", "nearly hit": "near miss collision",
    "worker fainted": "worker unconscious", "passed out": "worker unconscious",
}

def fold_unicode(value: str) -> str:
    """Normalize unicode accents and compatibility characters."""
    return unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")

@lru_cache(maxsize=100000)
def normalize_text(value: str) -> str:
    """Return a stable lower-case representation while preserving useful digits."""
    text = fold_unicode(value).lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def expand_common_phrases(value: str) -> str:
    """Expand colloquial worker language into standard safety vocabulary."""
    text = normalize_text(value)
    for phrase, replacement in sorted(COMMON_REPLACEMENTS.items(), key=lambda item: -len(item[0])):
        text = re.sub(r"\b" + re.escape(normalize_text(phrase)) + r"\b", replacement, text)
    return text

@lru_cache(maxsize=250000)
def contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = " " + normalize_text(text) + " "
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return False
    return " " + normalized_phrase + " " in normalized_text

def similarity(left: str, right: str) -> float:
    """Conservative typo similarity used only as a secondary clue."""
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()

def tokens(value: str) -> list[str]:
    return [token for token in normalize_text(value).split() if token]

def has_negation(text: str, phrase: str) -> bool:
    """Detect simple negation immediately before a phrase to reduce false alarms."""
    normalized = normalize_text(text)
    target = normalize_text(phrase)
    pattern = r"\b(?:no|not|never|without|isnt|wasnt|didnt)\s+(?:\w+\s+){0,2}" + re.escape(target) + r"\b"
    return re.search(pattern, normalized) is not None
