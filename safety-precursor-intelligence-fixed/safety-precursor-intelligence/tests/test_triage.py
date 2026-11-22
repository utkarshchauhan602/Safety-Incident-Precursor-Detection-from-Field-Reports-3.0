"""Regression tests for safety language detection and emergency prioritization."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spi.triage import detect_hazard, is_safety_domain
from spi.conversation import respond
from spi.models import ConversationState
from spi.scenario_catalog import SCENARIOS

def test_all_curated_scenarios_are_detected():
    failures=[]
    for item in SCENARIOS:
        match=detect_hazard(item["text"])
        if match is None or match.key != item["hazard"]:
            failures.append((item["id"], item["hazard"], match.key if match else None, item["text"]))
    assert not failures, failures[:25]

def test_electric_shock_is_critical():
    result=respond("worker got electric shock")
    assert result.hazard and result.hazard.key == "electric_shock"
    assert result.requires_attention
    assert "emergency" in result.text.lower()

def test_sleeping_during_shift_is_fatigue():
    result=respond("worker slept during shift")
    assert result.hazard and result.hazard.key == "fatigue"
    assert "fatigue" in result.text.lower()

def test_unrelated_text_is_not_misclassified_as_hazard():
    assert detect_hazard("the cafeteria menu changed today") is None

def test_short_follow_up_retains_electric_context():
    state=ConversationState(pending_intent="electric_shock")
    result=respond("power is off", state=state, use_generation=False)
    assert "medical" in result.text.lower()

def test_safety_domain_recognizes_worker_shift():
    assert is_safety_domain("worker slept during shift")
