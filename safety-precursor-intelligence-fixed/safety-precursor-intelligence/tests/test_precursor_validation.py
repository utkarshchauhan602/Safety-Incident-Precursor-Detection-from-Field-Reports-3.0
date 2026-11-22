import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from spi.precursor_validation import evaluate_precursors


def test_lead_time_requires_same_event_and_site():
    p = pd.DataFrame([
        {"event_id": "E1", "site": "A", "report_date": "2026-01-01"},
        {"event_id": "E2", "site": "A", "report_date": "2026-01-01"},
    ])
    i = pd.DataFrame([
        {"event_id": "E1", "site": "A", "incident_date": "2026-01-11"},
        {"event_id": "E2", "site": "B", "incident_date": "2026-01-21"},
    ])
    result = evaluate_precursors(p, i)
    assert result.matched_events == 1
    assert result.median_lead_time_days == 10
    assert result.excluded_unlinked_precursors == 1


def test_site_precision_excludes_unknown_follow_up():
    p = pd.DataFrame(columns=["event_id", "site", "report_date"])
    i = pd.DataFrame(columns=["event_id", "site", "incident_date"])
    flags = pd.DataFrame([
        {"site": "A", "outcome_observed": True, "incident_within_window": True},
        {"site": "B", "outcome_observed": True, "incident_within_window": False},
        {"site": "C", "outcome_observed": False, "incident_within_window": None},
    ])
    result = evaluate_precursors(p, i, flags)
    assert result.flagged_site_precision == 0.5
    assert result.excluded_unknown_site_outcomes == 1


def test_missing_linkage_columns_raise_clear_error():
    try:
        evaluate_precursors(pd.DataFrame(), pd.DataFrame())
    except ValueError as exc:
        assert "event_id" in str(exc)
    else:
        raise AssertionError("expected a schema validation error")
