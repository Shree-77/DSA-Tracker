"""Data-access for DailyTracker."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyTracker


class TrackerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, tracker: DailyTracker) -> DailyTracker:
        self.db.add(tracker)
        return tracker

    def get_by_study_day(self, study_day_id: int) -> DailyTracker | None:
        stmt = select(DailyTracker).where(
            DailyTracker.study_day_id == study_day_id
        )
        return self.db.execute(stmt).scalar_one_or_none()
