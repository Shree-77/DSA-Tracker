"""Plan schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PlanCreate(BaseModel):
    """Metadata used when creating a plan (optional overrides on import)."""

    name: str | None = None
    description: str | None = None


class PlanResponse(BaseModel):
    """Canonical plan representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    total_days: int
    created_at: datetime
    updated_at: datetime


class ImportSummary(BaseModel):
    """Returned after a successful import."""

    plan: PlanResponse
    total_days: int
    total_weeks: int
    total_phases: int
    start_date: date
    end_date: date
    trackers_imported: int = 0


class PhaseSummary(BaseModel):
    name: str
    days: int


class ImportPreviewResponse(BaseModel):
    """Returned by the preview endpoint (no data committed)."""

    valid: bool
    plan_name: str
    total_days: int
    total_weeks: int
    total_phases: int
    phases: list[PhaseSummary] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    errors: list[str] = Field(default_factory=list)
    trackers_detected: int = 0
