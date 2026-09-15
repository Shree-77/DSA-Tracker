"""Excel (.xlsx) workbook parser for DSA plans.

Responsibilities:
  * Tolerate minor header/formatting differences (case, spaces, punctuation).
  * Map "Problems / Task" -> internal ``task`` field, etc.
  * Validate required columns, row values, day numbers, difficulty, status.
  * Parse the optional "Daily Tracker" sheet.

The parser is *pure* (no DB access): it returns structured data plus a list of
human-readable errors. The service layer decides whether to commit.
"""

from __future__ import annotations

import io
import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import pandas as pd

from app.models.enums import StudyStatus

PLAN_SHEET_CANDIDATES = ["DSA Plan", "Plan", "Sheet1"]
TRACKER_SHEET_CANDIDATES = ["Daily Tracker", "Tracker"]
OVERVIEW_SHEET_CANDIDATES = ["Overview", "Meta", "Summary"]

VALID_DIFFICULTIES = {"easy", "medium", "hard", "mixed"}


@dataclass
class ParsedDay:  # pylint: disable=too-many-instance-attributes
    day_number: int
    week_number: int | None
    phase: str | None
    focus: str | None
    task: str | None
    difficulty: str | None
    status: StudyStatus
    completed_date: date | None
    notes: str | None


@dataclass
class ParsedTracker:  # pylint: disable=too-many-instance-attributes
    day_number: int
    study_date: date | None
    study_hours: float
    problems_attempted: int
    solved_alone: int
    needed_hint: int
    needed_solution: int
    confidence: int | None
    reflection: str | None


@dataclass
class ParseResult:
    plan_name: str
    description: str | None
    days: list[ParsedDay] = field(default_factory=list)
    trackers: list[ParsedTracker] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors and bool(self.days)


def _normalise_header(name: Any) -> str:
    """Lowercase, strip, and collapse punctuation/whitespace in a header."""
    text = str(name).strip().lower()
    text = re.sub(r"[\s/_\-]+", " ", text)
    text = re.sub(r"[^\w ]+", "", text)
    return text.strip()


# Map of internal-field -> set of accepted normalised header variants.
PLAN_COLUMN_ALIASES: dict[str, set[str]] = {
    "day": {"day", "day number", "dayno", "day no", "day num"},
    "week": {"week", "week number", "weekno"},
    "phase": {"phase", "topic", "module"},
    "focus": {"focus", "subtopic", "focus area"},
    "task": {
        "task",
        "problems task",
        "problems tasks",
        "problem task",
        "problems",
        "problem",
        "tasks",
    },
    "difficulty": {"difficulty", "level"},
    "status": {"status", "state"},
    "completed_date": {"completed date", "completion date", "done date"},
    "notes": {"notes", "note", "remarks"},
}

TRACKER_COLUMN_ALIASES: dict[str, set[str]] = {
    "day": {"day", "day number"},
    "date": {"date", "study date"},
    "study_hours": {"study hours", "hours", "time", "study time"},
    "problems_attempted": {"problems attempted", "attempted"},
    "solved_alone": {"solved alone", "solved"},
    "needed_hint": {"needed hint", "hint", "hints", "needed hints"},
    "needed_solution": {"needed solution", "solution", "solutions"},
    "confidence": {"confidence 15", "confidence", "confidence 1 5"},
    "reflection": {"reflection", "notes", "reflections"},
}

REQUIRED_PLAN_FIELDS = {"day"}

# User-facing labels for internal field names (used in error messages).
FIELD_LABELS: dict[str, str] = {
    "day": "Day",
    "week": "Week",
    "phase": "Phase",
    "focus": "Focus",
    "task": "Problems / Task",
    "difficulty": "Difficulty",
    "status": "Status",
    "completed_date": "Completed Date",
    "notes": "Notes",
}


def _build_column_map(
    df_columns: list[Any], aliases: dict[str, set[str]]
) -> dict[str, str]:
    """Return internal_field -> actual dataframe column name."""
    normalised = {col: _normalise_header(col) for col in df_columns}
    mapping: dict[str, str] = {}
    for field_name, variants in aliases.items():
        for actual, norm in normalised.items():
            if norm in variants:
                mapping[field_name] = actual
                break
    return mapping


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() == ""


def _clean_str(value: Any) -> str | None:
    if _is_blank(value):
        return None
    return str(value).strip()


def _to_int(value: Any) -> int | None:
    if _is_blank(value):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _to_float(value: Any, default: float = 0.0) -> float:
    if _is_blank(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _to_date(value: Any) -> date | None:
    if _is_blank(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    try:  # pandas fallback
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.notna(parsed):
            return parsed.date()
    except Exception:  # noqa: BLE001
        pass
    return None


def _pick_sheet(sheets: dict[str, pd.DataFrame], candidates: list[str]) -> str | None:
    lower_map = {name.strip().lower(): name for name in sheets}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def parse_workbook(content: bytes, plan_name: str | None = None) -> ParseResult:
    """Parse an .xlsx workbook (bytes) into a ParseResult.

    Never raises for content problems; instead accumulates messages in
    ``result.errors`` so the caller can present them clearly.
    """
    errors: list[str] = []
    try:
        sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        return ParseResult(
            plan_name=plan_name or "Imported Plan",
            description=None,
            errors=[f"Unable to read Excel workbook: {exc}"],
        )

    # --- Overview / metadata (best effort) ---------------------------------
    description = None
    overview_name = _pick_sheet(sheets, OVERVIEW_SHEET_CANDIDATES)
    resolved_name = plan_name
    if overview_name is not None:
        resolved_name, description = _read_overview(sheets[overview_name], resolved_name)

    # --- Plan sheet (required) ---------------------------------------------
    plan_sheet_name = _pick_sheet(sheets, PLAN_SHEET_CANDIDATES)
    if plan_sheet_name is None:
        # Fall back to the first sheet.
        plan_sheet_name = next(iter(sheets), None)
    if plan_sheet_name is None:
        errors.append("Workbook contains no sheets.")
        return ParseResult(plan_name=resolved_name or "Imported Plan", description=description, errors=errors)

    plan_df = sheets[plan_sheet_name]
    days, plan_errors = _parse_plan_sheet(plan_df)
    errors.extend(plan_errors)

    # --- Tracker sheet (optional) ------------------------------------------
    trackers: list[ParsedTracker] = []
    tracker_sheet_name = _pick_sheet(sheets, TRACKER_SHEET_CANDIDATES)
    if tracker_sheet_name is not None:
        valid_day_numbers = {d.day_number for d in days}
        trackers = _parse_tracker_sheet(sheets[tracker_sheet_name], valid_day_numbers)

    if not resolved_name:
        resolved_name = "DSA Preparation Plan"

    return ParseResult(
        plan_name=resolved_name,
        description=description,
        days=days,
        trackers=trackers,
        errors=errors,
    )


def _read_overview(df: pd.DataFrame, default_name: str | None) -> tuple[str | None, str | None]:
    """Extract a plan name/description from a key/value-style Overview sheet."""
    name = default_name
    description = None
    try:
        for _, row in df.iterrows():
            cells = [c for c in row.tolist() if not _is_blank(c)]
            if len(cells) < 2:
                continue
            key = _normalise_header(cells[0])
            value = _clean_str(cells[1])
            if key in {"plan", "plan name", "name", "title"} and value:
                name = value
            elif key in {"description", "desc", "goal", "objective"} and value:
                description = value
    except Exception:  # noqa: BLE001
        pass
    return name, description


def _parse_plan_sheet(df: pd.DataFrame) -> tuple[list[ParsedDay], list[str]]:
    errors: list[str] = []
    columns = list(df.columns)
    colmap = _build_column_map(columns, PLAN_COLUMN_ALIASES)

    missing = REQUIRED_PLAN_FIELDS - set(colmap)
    if missing:
        pretty = ", ".join(
            sorted(f'"{FIELD_LABELS.get(m, m)}"' for m in missing)
        )
        errors.append(f"Missing required column(s): {pretty}.")
        return [], errors

    days: list[ParsedDay] = []
    seen_day_numbers: set[int] = set()

    for idx, row in df.iterrows():
        # Excel row number: header is row 1, data starts at row 2.
        excel_row = int(idx) + 2  # type: ignore[arg-type]

        raw_day = row[colmap["day"]] if colmap.get("day") in row else None
        # Skip fully-blank rows silently.
        if all(_is_blank(row[c]) for c in columns):
            continue

        day_number = _to_int(raw_day)
        if day_number is None:
            errors.append(f"Row {excel_row}: Day number is missing.")
            continue
        if day_number <= 0:
            errors.append(f"Row {excel_row}: Day number must be positive.")
            continue
        if day_number in seen_day_numbers:
            errors.append(f"Row {excel_row}: Duplicate day number {day_number}.")
            continue
        seen_day_numbers.add(day_number)

        difficulty = _clean_str(row[colmap["difficulty"]]) if colmap.get("difficulty") else None
        if difficulty is not None and difficulty.lower() not in VALID_DIFFICULTIES:
            errors.append(
                f"Row {excel_row}: Invalid difficulty {difficulty!r} "
                f"(expected Easy/Medium/Hard/Mixed)."
            )
            continue

        status_val = row[colmap["status"]] if colmap.get("status") else None
        try:
            status = StudyStatus.from_raw(_clean_str(status_val))
        except ValueError:
            errors.append(
                f"Row {excel_row}: Invalid status "
                f"{_clean_str(status_val)!r}."
            )
            continue

        days.append(
            ParsedDay(
                day_number=day_number,
                week_number=_to_int(row[colmap["week"]]) if colmap.get("week") else None,
                phase=_clean_str(row[colmap["phase"]]) if colmap.get("phase") else None,
                focus=_clean_str(row[colmap["focus"]]) if colmap.get("focus") else None,
                task=_clean_str(row[colmap["task"]]) if colmap.get("task") else None,
                difficulty=difficulty.capitalize() if difficulty else None,
                status=status,
                completed_date=_to_date(row[colmap["completed_date"]])
                if colmap.get("completed_date")
                else None,
                notes=_clean_str(row[colmap["notes"]]) if colmap.get("notes") else None,
            )
        )

    if not days and not errors:
        errors.append("No study days found in the plan sheet.")

    # Sort by day number for deterministic ordering.
    days.sort(key=lambda d: d.day_number)
    return days, errors


def _parse_tracker_sheet(
    df: pd.DataFrame, valid_day_numbers: set[int]
) -> list[ParsedTracker]:
    colmap = _build_column_map(list(df.columns), TRACKER_COLUMN_ALIASES)
    if "day" not in colmap:
        return []

    trackers: list[ParsedTracker] = []
    for _, row in df.iterrows():
        day_number = _to_int(row[colmap["day"]])
        if day_number is None or day_number not in valid_day_numbers:
            continue

        confidence = _to_int(row[colmap["confidence"]]) if colmap.get("confidence") else None
        if confidence is not None and not 1 <= confidence <= 5:
            confidence = None  # tolerate out-of-range tracker imports silently

        has_data = any(
            not _is_blank(row[colmap[f]])
            for f in (
                "study_hours",
                "problems_attempted",
                "solved_alone",
                "needed_hint",
                "needed_solution",
                "confidence",
                "reflection",
            )
            if colmap.get(f)
        )
        if not has_data:
            continue

        trackers.append(
            ParsedTracker(
                day_number=day_number,
                study_date=_to_date(row[colmap["date"]]) if colmap.get("date") else None,
                study_hours=_to_float(row[colmap["study_hours"]]) if colmap.get("study_hours") else 0.0,
                problems_attempted=_to_int(row[colmap["problems_attempted"]]) or 0
                if colmap.get("problems_attempted")
                else 0,
                solved_alone=_to_int(row[colmap["solved_alone"]]) or 0
                if colmap.get("solved_alone")
                else 0,
                needed_hint=_to_int(row[colmap["needed_hint"]]) or 0
                if colmap.get("needed_hint")
                else 0,
                needed_solution=_to_int(row[colmap["needed_solution"]]) or 0
                if colmap.get("needed_solution")
                else 0,
                confidence=confidence,
                reflection=_clean_str(row[colmap["reflection"]]) if colmap.get("reflection") else None,
            )
        )
    return trackers
