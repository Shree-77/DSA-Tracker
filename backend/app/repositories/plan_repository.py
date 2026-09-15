"""Data-access for Plan (and cascaded StudyDay/DailyTracker rows).

All read/lookup methods are scoped by ``user_id`` so one user can never see or
mutate another user's plans.
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models import Plan, StudyDay
from app.models.enums import PlanStatus, StudyStatus


class PlanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: int,
        name: str,
        description: str | None,
        total_days: int,
        *,
        select_as_active: bool = True,
    ) -> Plan:
        if select_as_active:
            # Only one plan may be selected at a time; deselect the rest first.
            self.deselect_all(user_id)
        plan = Plan(
            user_id=user_id,
            name=name,
            description=description,
            total_days=total_days,
            is_selected=select_as_active,
        )
        self.db.add(plan)
        self.db.flush()  # populate plan.id without committing
        return plan

    def get(self, plan_id: int, user_id: int) -> Plan | None:
        stmt = select(Plan).where(Plan.id == plan_id, Plan.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_with_days(self, plan_id: int, user_id: int) -> Plan | None:
        stmt = (
            select(Plan)
            .where(Plan.id == plan_id, Plan.user_id == user_id)
            .options(selectinload(Plan.days).selectinload(StudyDay.tracker))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, user_id: int, status: PlanStatus | None = None) -> list[Plan]:
        stmt = select(Plan).where(Plan.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Plan.status == status)
        stmt = stmt.order_by(Plan.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_active(self, user_id: int) -> Plan | None:
        """Return the user's currently *selected* plan.

        Falls back to the most recently created plan if none is explicitly
        selected yet (e.g. data created before selection existed).
        """
        stmt = select(Plan).where(
            Plan.user_id == user_id, Plan.is_selected.is_(True)
        )
        selected = self.db.execute(stmt).scalar_one_or_none()
        if selected is not None:
            return selected

        stmt = (
            select(Plan)
            .where(Plan.user_id == user_id)
            .order_by(Plan.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def deselect_all(self, user_id: int) -> None:
        stmt = (
            update(Plan)
            .where(Plan.user_id == user_id, Plan.is_selected.is_(True))
            .values(is_selected=False)
        )
        self.db.execute(stmt)

    def select_plan(self, plan: Plan) -> None:
        """Make ``plan`` the user's selected/active plan; deselect all others."""
        self.deselect_all(plan.user_id)
        plan.is_selected = True
        self.db.flush()

    def day_counts(self, plan_id: int) -> tuple[int, int]:
        """Return ``(total_days, remaining_days)`` for a plan.

        A day is "remaining" when it is neither DONE nor SKIPPED. A plan is
        considered complete when it has at least one day and zero remaining.
        """
        terminal = {StudyStatus.DONE, StudyStatus.SKIPPED}
        statuses = self.db.execute(
            select(StudyDay.status).where(StudyDay.plan_id == plan_id)
        ).scalars().all()
        total = len(statuses)
        remaining = sum(1 for s in statuses if s not in terminal)
        return total, remaining

    def delete(self, plan: Plan) -> None:
        self.db.delete(plan)
        self.db.flush()
