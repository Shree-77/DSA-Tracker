"""Progress schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WeeklyProgress(BaseModel):
    week_number: int
    phase: str | None = None
    total: int
    completed: int


class DifficultyBreakdown(BaseModel):
    difficulty: str
    total: int
    completed: int


class ProgressResponse(BaseModel):
    """Aggregate progress + statistics for a plan."""

    total_days: int
    completed_days: int
    remaining_days: int
    completion_percentage: float

    current_streak: int
    longest_streak: int

    total_study_hours: float
    problems_attempted: int
    solved_alone: int
    needed_hint: int
    needed_solution: int
    average_confidence: float | None = None

    weekly: list[WeeklyProgress] = Field(default_factory=list)
    difficulty: list[DifficultyBreakdown] = Field(default_factory=list)
