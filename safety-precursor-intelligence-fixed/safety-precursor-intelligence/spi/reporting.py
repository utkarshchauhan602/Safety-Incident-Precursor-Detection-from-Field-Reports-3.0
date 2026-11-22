"""Incident report drafting and export helpers."""
from __future__ import annotations
from datetime import datetime, timezone
from html import escape
from typing import Any

def draft_incident_report(description: str, site: str, department: str, equipment: str = "Not specified", category: str = "Pending review", risk: str = "Pending review") -> dict[str, Any]:
    clean = " ".join(str(description).split())
    return {"report_id": "SPI-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "created_at_utc": datetime.now(timezone.utc).isoformat(), "site": site,
            "department": department, "equipment_or_area": equipment or "Not specified",
            "description": clean, "predicted_category": category, "screening_level": risk,
            "status": "Open - supervisor review required",
            "review_note": "AI-assisted screening only. Verify facts and risk with a competent site representative."}

def report_markdown(report: dict[str, Any]) -> str:
    rows = ["# Workplace Safety Incident / Observation Report", "",
            f"**Reference:** {report.get('report_id', 'Draft')}",
            f"**Created (UTC):** {report.get('created_at_utc', 'Not recorded')}",
            f"**Site:** {report.get('site', 'Not specified')}",
            f"**Department:** {report.get('department', 'Not specified')}",
            f"**Equipment / area:** {report.get('equipment_or_area', 'Not specified')}",
            f"**Predicted category:** {report.get('predicted_category', 'Pending review')}",
            f"**Screening level:** {report.get('screening_level', 'Pending review')}", "",
            "## Description", "", report.get("description", "No description supplied"), "",
            "## Review status", "", report.get("status", "Pending"), "",
            report.get("review_note", "Human verification required.")]
    return "\n".join(rows)

def report_html(report: dict[str, Any]) -> str:
    fields = ("report_id", "created_at_utc", "site", "department", "equipment_or_area", "predicted_category", "screening_level", "status")
    table = "".join(f"<tr><th>{escape(label.replace('_', ' ').title())}</th><td>{escape(str(report.get(label, '')))}</td></tr>" for label in fields)
    description = escape(str(report.get("description", "")))
    return "<!doctype html><html><head><meta charset='utf-8'><title>Safety Report</title></head><body><h1>Safety Report</h1><table>" + table + "</table><h2>Description</h2><p>" + description + "</p><p>AI-assisted screening; competent human review required.</p></body></html>"
