"""Pure dataframe analytics used by dashboard and conversational answers."""
from __future__ import annotations
from typing import Any
import pandas as pd

REQUIRED_COLUMNS = ("report_date", "site", "department", "category", "risk_level", "report_text", "status")

def ensure_schema(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    for column in REQUIRED_COLUMNS:
        if column not in data.columns:
            data[column] = pd.Series(dtype="object")
    data["report_date"] = pd.to_datetime(data["report_date"], errors="coerce")
    return data

def summary(frame: pd.DataFrame) -> dict[str, int]:
    data = ensure_schema(frame)
    return {"total": int(len(data)), "high": int((data["risk_level"] == "High").sum()),
            "open": int((data["status"] == "Open").sum()), "closed": int((data["status"] == "Closed").sum()),
            "sites": int(data["site"].nunique(dropna=True))}

def top_sites(frame: pd.DataFrame, limit: int = 5) -> pd.Series:
    return ensure_schema(frame)["site"].value_counts().head(max(1, limit))

def category_counts(frame: pd.DataFrame) -> pd.Series:
    return ensure_schema(frame)["category"].value_counts(dropna=False)

def filter_period(frame: pd.DataFrame, days: int | None = None, start=None, end=None) -> pd.DataFrame:
    data = ensure_schema(frame)
    if start is not None:
        data = data[data["report_date"] >= pd.Timestamp(start)]
    if end is not None:
        data = data[data["report_date"] <= pd.Timestamp(end)]
    if days is not None:
        cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=days)
        data = data[data["report_date"] >= cutoff]
    return data

def recurring_hazards(frame: pd.DataFrame, minimum: int = 3) -> list[dict[str, Any]]:
    data = ensure_schema(frame)
    if data.empty:
        return []
    grouped = data.groupby(["site", "category"], dropna=False).size().reset_index(name="count")
    grouped = grouped[grouped["count"] >= minimum].sort_values("count", ascending=False)
    return grouped.to_dict(orient="records")

def open_actions(frame: pd.DataFrame) -> pd.DataFrame:
    data = ensure_schema(frame)
    return data[data["status"].isin(["Open", "In Progress"])].copy()
