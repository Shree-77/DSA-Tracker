"""StudyDay schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StudyStatus


class StudyDayResponse(BaseModel):
    """Canonical representation of a study day returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    day_number: int
    week_number: int | None = None
    phase: str | None = None
    focus: str | None = None
    task: str | None = None
    difficulty: str | None = None
    status: StudyStatus
    scheduled_date: date | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class StudyDayUpdate(BaseModel):
    """Partial update payload for a study day (PATCH)."""

    status: StudyStatus | None = None
    notes: str | None = None
    focus: str | None = None
    task: str | None = None
    difficulty: str | None = None


class TodayResponse(BaseModel):
    """Response for the 'today' endpoint.

    ``state`` describes where the user is relative to the plan window:
      - "before"   -> plan has not started yet (days_until_start set)
      - "active"   -> there is a study day for today (day set)
      - "completed"-> today is past the final scheduled day
      - "empty"    -> plan has no days
    """

    state: str
    day: StudyDayResponse | None = None
    upcoming: list[StudyDayResponse] = Field(default_factory=list)
    days_until_start: int | None = None
    total_days: int = 0
    completed_days: int = 0
    completion_percentage: float = 0.0
    message: str | None = None
