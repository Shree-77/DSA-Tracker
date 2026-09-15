"""Plan service: plan retrieval, today's day, and deletion."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Plan
from app.repositories import PlanRepository, StudyDayRepository
from app.schemas.plan import PlanResponse
from app.schemas.study_day import StudyDayResponse, TodayResponse


class PlanService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.plans = PlanRepository(db)
        self.days = StudyDayRepository(db)

    def list_plans(self) -> list[PlanResponse]:
        return [PlanResponse.model_validate(p) for p in self.plans.list()]

    def get_plan(self, plan_id: int) -> PlanResponse:
        plan = self._require_plan(plan_id)
        return PlanResponse.model_validate(plan)

    def delete_plan(self, plan_id: int) -> None:
        plan = self._require_plan(plan_id)
        self.plans.delete(plan)
        self.db.commit()

    def list_days(self, plan_id: int) -> list[StudyDayResponse]:
        self._require_plan(plan_id)
        days = self.days.list_for_plan(plan_id)
        return [StudyDayResponse.model_validate(d) for d in days]

    def get_today(self, plan_id: int, today: date | None = None) -> TodayResponse:
        plan = self._require_plan(plan_id)
        today = today or date.today()

        days = self.days.list_for_plan(plan_id)
        if not days:
            return TodayResponse(state="empty", total_days=0, message="This plan has no days.")

        completed = sum(1 for d in days if d.status.value == "DONE")
        total = len(days)
        pct = round((completed / total) * 100, 2) if total else 0.0

        scheduled = [d for d in days if d.scheduled_date is not None]
        start = min((d.scheduled_date for d in scheduled), default=None)
        end = max((d.scheduled_date for d in scheduled), default=None)

        # Before the plan starts.
        if start is not None and today < start:
            days_until = (start - today).days
            return TodayResponse(
                state="before",
                days_until_start=days_until,
                total_days=total,
                completed_days=completed,
                completion_percentage=pct,
                message=f"Your plan starts in {days_until} day"
                + ("s" if days_until != 1 else "")
                + ".",
            )

        # After the last scheduled day.
        if end is not None and today > end:
            return TodayResponse(
                state="completed",
                total_days=total,
                completed_days=completed,
                completion_percentage=pct,
                message="Plan completed 🎉",
            )

        today_day = self.days.get_by_scheduled_date(plan_id, today)
        upcoming = self.days.upcoming(plan_id, today, limit=3)

        return TodayResponse(
            state="active",
            day=StudyDayResponse.model_validate(today_day) if today_day else None,
            upcoming=[StudyDayResponse.model_validate(d) for d in upcoming],
            total_days=total,
            completed_days=completed,
            completion_percentage=pct,
        )

    def _require_plan(self, plan_id: int) -> Plan:
        plan = self.plans.get(plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {plan_id} not found", code="PLAN_NOT_FOUND")
        return plan
