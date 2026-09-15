"""Data-access for Plan (and cascaded StudyDay/DailyTracker rows)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Plan, StudyDay


class PlanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, name: str, description: str | None, total_days: int) -> Plan:
        plan = Plan(name=name, description=description, total_days=total_days)
        self.db.add(plan)
        self.db.flush()  # populate plan.id without committing
        return plan

    def get(self, plan_id: int) -> Plan | None:
        return self.db.get(Plan, plan_id)

    def get_with_days(self, plan_id: int) -> Plan | None:
        stmt = (
            select(Plan)
            .where(Plan.id == plan_id)
            .options(selectinload(Plan.days).selectinload(StudyDay.tracker))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self) -> list[Plan]:
        stmt = select(Plan).order_by(Plan.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_active(self) -> Plan | None:
        """Return the most recently created plan (single-user 'active' plan)."""
        stmt = select(Plan).order_by(Plan.created_at.desc()).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def delete(self, plan: Plan) -> None:
        self.db.delete(plan)
        self.db.flush()
