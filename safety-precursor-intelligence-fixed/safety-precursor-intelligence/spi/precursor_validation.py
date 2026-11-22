"""Outcome-linked precursor validation metrics.

Metrics are intentionally unavailable unless precursor observations can be linked
 to subsequent recorded incidents. Site flags must also have an outcome window
and an observed outcome; unknown outcomes are not silently counted as negatives.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import pandas as pd


@dataclass(frozen=True)
class ValidationMetrics:
    matched_events: int
    median_lead_time_days: float | None
    mean_lead_time_days: float | None
    flagged_sites: int
    flagged_sites_with_incident: int
    flagged_site_precision: float | None
    excluded_unlinked_precursors: int
    excluded_unknown_site_outcomes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _dates(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(frame[column], errors="coerce", utc=True)


def evaluate_precursors(
    precursors: pd.DataFrame,
    incidents: pd.DataFrame,
    site_flags: pd.DataFrame | None = None,
) -> ValidationMetrics:
    """Calculate lead time and flagged-site precision from linked, dated records.

    Required precursor columns: event_id, site, report_date.
    Required incident columns: event_id, site, incident_date.
    Optional site_flags columns: site, flagged_at, outcome_observed, incident_within_window.

    `incident_within_window` must be populated only after the full, pre-defined
    follow-up window has elapsed. Incomplete follow-up is marked unknown.
    """
    p_required = {"event_id", "site", "report_date"}
    i_required = {"event_id", "site", "incident_date"}
    if not p_required.issubset(precursors.columns):
        raise ValueError(f"precursors missing columns: {sorted(p_required - set(precursors.columns))}")
    if not i_required.issubset(incidents.columns):
        raise ValueError(f"incidents missing columns: {sorted(i_required - set(incidents.columns))}")

    p = precursors.copy()
    i = incidents.copy()
    p["_precursor_date"] = _dates(p, "report_date")
    i["_incident_date"] = _dates(i, "incident_date")
    p = p.dropna(subset=["event_id", "site", "_precursor_date"])
    i = i.dropna(subset=["event_id", "site", "_incident_date"])
    linked = p.merge(i, on=["event_id", "site"], how="inner")
    linked["lead_days"] = (linked["_incident_date"] - linked["_precursor_date"]).dt.total_seconds() / 86400
    # Negative/zero intervals are invalid as a precursor lead time.
    linked = linked[linked["lead_days"] > 0]
    leads = linked["lead_days"]
    matched_keys = set(zip(linked["event_id"], linked["site"]))
    excluded_unlinked = sum((row.event_id, row.site) not in matched_keys for row in p[["event_id", "site"]].itertuples(index=False))

    flagged_count = with_incident = unknown = 0
    precision = None
    if site_flags is not None and not site_flags.empty:
        required = {"site", "outcome_observed", "incident_within_window"}
        if not required.issubset(site_flags.columns):
            raise ValueError(f"site_flags missing columns: {sorted(required - set(site_flags.columns))}")
        flags = site_flags.copy()
        flags = flags[flags["site"].notna()]
        flagged_count = int(flags["site"].nunique())
        observed = flags[flags["outcome_observed"].astype("boolean").fillna(False)]
        unknown = int(flags["site"].nunique() - observed["site"].nunique())
        # One site counts as a true positive if any observed flag window had an incident.
        positives = observed[observed["incident_within_window"].astype("boolean").fillna(False)]
        with_incident = int(positives["site"].nunique())
        evaluated_sites = int(observed["site"].nunique())
        precision = (with_incident / evaluated_sites) if evaluated_sites else None

    return ValidationMetrics(
        matched_events=int(len(linked)),
        median_lead_time_days=round(float(leads.median()), 2) if len(leads) else None,
        mean_lead_time_days=round(float(leads.mean()), 2) if len(leads) else None,
        flagged_sites=flagged_count,
        flagged_sites_with_incident=with_incident,
        flagged_site_precision=round(float(precision), 4) if precision is not None else None,
        excluded_unlinked_precursors=int(excluded_unlinked),
        excluded_unknown_site_outcomes=unknown,
    )
