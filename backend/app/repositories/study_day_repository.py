"""Data-access for StudyDay."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import StudyDay


class StudyDayRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, day: StudyDay) -> StudyDay:
        self.db.add(day)
        return day

    def bulk_add(self, days: list[StudyDay]) -> None:
        self.db.add_all(days)

    def get(self, study_day_id: int) -> StudyDay | None:
        return self.db.get(StudyDay, study_day_id)

    def get_with_tracker(self, study_day_id: int) -> StudyDay | None:
        stmt = (
            select(StudyDay)
            .where(StudyDay.id == study_day_id)
            .options(selectinload(StudyDay.tracker))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_plan_and_day(self, plan_id: int, day_number: int) -> StudyDay | None:
        stmt = select(StudyDay).where(
            StudyDay.plan_id == plan_id, StudyDay.day_number == day_number
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_plan(self, plan_id: int) -> list[StudyDay]:
        stmt = (
            select(StudyDay)
            .where(StudyDay.plan_id == plan_id)
            .order_by(StudyDay.day_number)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_scheduled_date(
        self, plan_id: int, on_date: date
    ) -> StudyDay | None:
        stmt = select(StudyDay).where(
            StudyDay.plan_id == plan_id, StudyDay.scheduled_date == on_date
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upcoming(
        self, plan_id: int, after_date: date, limit: int = 3
    ) -> list[StudyDay]:
        stmt = (
            select(StudyDay)
            .where(
                StudyDay.plan_id == plan_id,
                StudyDay.scheduled_date > after_date,
            )
            .order_by(StudyDay.scheduled_date)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
