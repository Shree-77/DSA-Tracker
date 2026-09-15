"""Build an in-memory .xlsx workbook from a structured plan dict.

This is the bridge between the AI (which returns JSON) and the existing import
pipeline (which consumes .xlsx). The generated workbook mirrors the exact sheet
layout that ``app.utils.excel_parser`` understands — "Study Plan", optional
"Daily Tracker", and "Overview" — so the AI-created plan flows through the same
validated ``ImportService`` used for manual uploads.
"""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

# Column headers must match the parser's accepted aliases.
_PLAN_COLUMNS = [
    "Day",
    "Week",
    "Phase",
    "Focus",
    "Problems / Task",
    "Difficulty",
    "Status",
    "Notes",
]

_VALID_DIFFICULTY = {"Easy", "Medium", "Hard", "Mixed"}


def _coerce_difficulty(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().capitalize()
    return text if text in _VALID_DIFFICULTY else None


def build_plan_workbook(plan: dict[str, Any]) -> bytes:
    """Convert a plan dict into .xlsx bytes ready for ImportService.

    Expected (tolerant) shape::

        {
          "name": "8-Week Python Plan",
          "description": "...",
          "days": [
            {"day": 1, "week": 1, "phase": "Basics", "focus": "Syntax",
             "task": "Variables & types", "difficulty": "Easy", "notes": ""},
            ...
          ]
        }

    Missing/extra fields are tolerated; only ``day`` is required per row and is
    re-numbered sequentially if absent to guarantee a valid workbook.
    """
    days_in = plan.get("days") or []
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(days_in, start=1):
        if not isinstance(raw, dict):
            continue
        day_number = raw.get("day") or raw.get("day_number") or index
        rows.append(
            {
                "Day": int(day_number),
                "Week": raw.get("week") or raw.get("week_number"),
                "Phase": raw.get("phase"),
                "Focus": raw.get("focus"),
                "Problems / Task": raw.get("task") or raw.get("problems"),
                "Difficulty": _coerce_difficulty(raw.get("difficulty")),
                "Status": "NOT_STARTED",
                "Notes": raw.get("notes"),
            }
        )

    plan_df = pd.DataFrame(rows, columns=_PLAN_COLUMNS)

    overview_df = pd.DataFrame(
        [
            {"Key": "Plan", "Value": plan.get("name") or "AI Study Plan"},
            {"Key": "Description", "Value": plan.get("description") or ""},
            {"Key": "Total Days", "Value": len(rows)},
        ]
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        plan_df.to_excel(writer, sheet_name="Study Plan", index=False)
        overview_df.to_excel(writer, sheet_name="Overview", index=False)
    return buffer.getvalue()
