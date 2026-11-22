"""Rule-first safety triage. Emergency patterns take precedence over language generation."""
from __future__ import annotations
from .knowledge import PLAYBOOKS, Playbook
from .models import HazardMatch
from .normalization import normalize_text, expand_common_phrases, contains_phrase

PRIORITY = ("electric_shock", "unconsciousness", "fire", "gas_release", "chemical_spill", "electrical_hazard",
            "ppe", "fall_height", "machine_guard", "fatigue", "vehicle", "slip_trip")

def _score(text: str, playbook: Playbook) -> tuple[float, tuple[str, ...]]:
    normalized = expand_common_phrases(text)
    # Match both the original wording and its normalized paraphrase. Phrase
    # expansion is additive: it must never erase the source clue needed by triage.
    matched = tuple(term for term in playbook.terms
                    if contains_phrase(text, term) or contains_phrase(normalized, term))
    if not matched:
        return 0.0, ()
    phrase_bonus = min(0.22, 0.06 * len(matched))
    length_bonus = 0.05 if len(normalized.split()) > 5 else 0.0
    confidence = min(0.99, 0.70 + phrase_bonus + length_bonus)
    return confidence, matched

def detect_hazard(text: str) -> HazardMatch | None:
    """Identify the strongest known hazard using deterministic priority ordering."""
    normalized = expand_common_phrases(text)
    if not normalized:
        return None
    matches: list[tuple[int, float, str, Playbook, tuple[str, ...]]] = []
    for priority, key in enumerate(PRIORITY):
        playbook = PLAYBOOKS[key]
        confidence, terms = _score(text, playbook)
        if confidence:
            matches.append((priority, confidence, key, playbook, terms))
    if not matches:
        return None
    # More specific emergency types are preferred; confidence breaks ties within a type.
    _, confidence, key, selected, terms = sorted(matches, key=lambda item: (item[0], -item[1]))[0]
    return HazardMatch(key=key, title=selected.title, category=selected.category,
                       severity=selected.severity, confidence=confidence,
                       matched_terms=terms, emergency=selected.emergency)

def classify_intent(text: str) -> str:
    value = normalize_text(text)
    if any(word in value for word in ("how many", "count", "reports this", "which site", "trend", "most common")):
        return "report_analytics"
    if any(word in value for word in ("hello", "hi", "good morning", "hey there")) and len(value.split()) < 5:
        return "greeting"
    if any(word in value for word in ("what is", "explain", "meaning", "define")):
        return "safety_explanation"
    if any(word in value for word in ("save report", "create report", "log this", "record this")):
        return "save_report"
    if detect_hazard(value):
        return "hazard_report"
    return "general_safety"

def is_safety_domain(text: str) -> bool:
    value = normalize_text(text)
    anchors = ("worker", "shift", "site", "safety", "hazard", "incident", "accident", "injury",
               "machine", "equipment", "chemical", "electric", "wire", "fire", "gas", "ppe",
               "near miss", "fall", "slip", "fatigue", "sleeping", "helmet", "forklift", "report")
    return any(anchor in value for anchor in anchors)
