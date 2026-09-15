"""Data-access for Plan (and cascaded StudyDay/DailyTracker rows).

All read/lookup methods are scoped by ``user_id`` so one user can never see or
mutate another user's plans.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Plan, StudyDay


class PlanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self, user_id: int, name: str, description: str | None, total_days: int
    ) -> Plan:
        plan = Plan(
            user_id=user_id,
            name=name,
            description=description,
            total_days=total_days,
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

    def list(self, user_id: int) -> list[Plan]:
        stmt = (
            select(Plan)
            .where(Plan.user_id == user_id)
            .order_by(Plan.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_active(self, user_id: int) -> Plan | None:
        """Return the user's most recently created plan (their 'active' plan)."""
        stmt = (
            select(Plan)
            .where(Plan.user_id == user_id)
            .order_by(Plan.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete(self, plan: Plan) -> None:
        self.db.delete(plan)
        self.db.flush()
