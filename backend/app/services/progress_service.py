"""Progress service: aggregate statistics, weekly breakdown, and streaks."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import StudyDay
from app.models.enums import StudyStatus
from app.repositories import PlanRepository, StudyDayRepository
from app.schemas.progress import (
    DifficultyBreakdown,
    ProgressResponse,
    WeeklyProgress,
)


class ProgressService:
    def __init__(self, db: Session, user_id: int) -> None:
        self.db = db
        self.user_id = user_id
        self.plans = PlanRepository(db)
        self.days = StudyDayRepository(db)

    def get_progress(self, plan_id: int, today: date | None = None) -> ProgressResponse:
        if self.plans.get(plan_id, self.user_id) is None:
            raise NotFoundError(f"Plan {plan_id} not found", code="PLAN_NOT_FOUND")

        today = today or date.today()
        plan = self.plans.get_with_days(plan_id, self.user_id)
        days = list(plan.days) if plan else []

        total = len(days)
        done_days = [d for d in days if d.status == StudyStatus.DONE]
        completed = len(done_days)
        remaining = total - completed
        pct = round((completed / total) * 100, 2) if total else 0.0

        current_streak, longest_streak = self._compute_streaks(done_days, today)
        stats = self._aggregate_tracker_stats(days)
        weekly = self._weekly_breakdown(days)
        difficulty = self._difficulty_breakdown(days)

        return ProgressResponse(
            total_days=total,
            completed_days=completed,
            remaining_days=remaining,
            completion_percentage=pct,
            current_streak=current_streak,
            longest_streak=longest_streak,
            weekly=weekly,
            difficulty=difficulty,
            **stats,
        )

    # -- streaks -------------------------------------------------------------
    @staticmethod
    def _completion_date(day: StudyDay) -> date | None:
        """Date a day counts toward the streak.

        A study day belongs to its *scheduled* calendar slot, so streaks are
        measured against ``scheduled_date`` (the day it was meant to be done).
        This keeps consecutive-day logic correct regardless of the wall-clock
        time at which the user actually pressed "Done". Falls back to the
        completion timestamp for ad-hoc days without a schedule.
        """
        if day.scheduled_date is not None:
            return day.scheduled_date
        if day.completed_at is not None:
            return day.completed_at.date()
        return None

    def _compute_streaks(
        self, done_days: list[StudyDay], today: date
    ) -> tuple[int, int]:
        """Return (current_streak, longest_streak) over consecutive dates.

        A day counts only when status == DONE. The current streak is the run of
        consecutive completed days ending at today or yesterday — so an
        as-yet-incomplete *today* does not break an otherwise unbroken streak.
        """
        dates = sorted({self._completion_date(d) for d in done_days if self._completion_date(d) is not None})
        if not dates:
            return 0, 0

        # Longest streak: longest run of consecutive calendar days.
        longest = 1
        run = 1
        for prev, cur in zip(dates, dates[1:]):
            if (cur - prev).days == 1:
                run += 1
            elif cur == prev:
                continue
            else:
                run = 1
            longest = max(longest, run)

        # Current streak: walk backwards from today (or yesterday).
        date_set = set(dates)
        anchor = today if today in date_set else today - timedelta(days=1)
        current = 0
        cursor = anchor
        while cursor in date_set:
            current += 1
            cursor -= timedelta(days=1)

        return current, longest

    # -- tracker stats -------------------------------------------------------
    @staticmethod
    def _aggregate_tracker_stats(days: list[StudyDay]) -> dict:
        total_hours = 0.0
        attempted = 0
        solved = 0
        hints = 0
        solutions = 0
        confidences: list[int] = []

        for d in days:
            tracker = d.tracker
            if tracker is None:
                continue
            total_hours += tracker.study_hours or 0.0
            attempted += tracker.problems_attempted or 0
            solved += tracker.solved_alone or 0
            hints += tracker.needed_hint or 0
            solutions += tracker.needed_solution or 0
            if tracker.confidence is not None:
                confidences.append(tracker.confidence)

        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else None

        return {
            "total_study_hours": round(total_hours, 2),
            "problems_attempted": attempted,
            "solved_alone": solved,
            "needed_hint": hints,
            "needed_solution": solutions,
            "average_confidence": avg_conf,
        }

    # -- weekly breakdown ----------------------------------------------------
    @staticmethod
    def _weekly_breakdown(days: list[StudyDay]) -> list[WeeklyProgress]:
        buckets: dict[int, dict] = {}
        for d in days:
            week = d.week_number if d.week_number is not None else 0
            bucket = buckets.setdefault(
                week, {"total": 0, "completed": 0, "phase": d.phase}
            )
            bucket["total"] += 1
            if d.status == StudyStatus.DONE:
                bucket["completed"] += 1
            if bucket["phase"] is None and d.phase:
                bucket["phase"] = d.phase

        return [
            WeeklyProgress(
                week_number=week,
                phase=data["phase"],
                total=data["total"],
                completed=data["completed"],
            )
            for week, data in sorted(buckets.items())
        ]

    # -- difficulty breakdown ------------------------------------------------
    @staticmethod
    def _difficulty_breakdown(days: list[StudyDay]) -> list[DifficultyBreakdown]:
        order = ["Easy", "Medium", "Hard", "Mixed"]
        buckets: dict[str, dict] = {}
        for d in days:
            key = (d.difficulty or "Unspecified").capitalize()
            bucket = buckets.setdefault(key, {"total": 0, "completed": 0})
            bucket["total"] += 1
            if d.status == StudyStatus.DONE:
                bucket["completed"] += 1

        def sort_key(name: str) -> int:
            return order.index(name) if name in order else len(order)

        return [
            DifficultyBreakdown(
                difficulty=name,
                total=buckets[name]["total"],
                completed=buckets[name]["completed"],
            )
            for name in sorted(buckets, key=sort_key)
        ]
