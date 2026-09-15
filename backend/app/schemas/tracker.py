"""DailyTracker schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class TrackerUpdate(BaseModel):
    """Upsert payload for a day's tracker (PUT)."""

    study_date: date | None = None
    study_hours: float = Field(default=0.0, ge=0)
    problems_attempted: int = Field(default=0, ge=0)
    solved_alone: int = Field(default=0, ge=0)
    needed_hint: int = Field(default=0, ge=0)
    needed_solution: int = Field(default=0, ge=0)
    confidence: int | None = Field(default=None, ge=1, le=5)
    reflection: str | None = None


class TrackerResponse(BaseModel):
    """Canonical tracker representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    study_day_id: int
    study_date: date | None = None
    study_hours: float
    problems_attempted: int
    solved_alone: int
    needed_hint: int
    needed_solution: int
    confidence: int | None = None
    reflection: str | None = None
