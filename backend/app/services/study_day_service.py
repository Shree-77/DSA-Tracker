"""Study day service: fetch/update days and upsert trackers."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import DailyTracker, StudyDay
from app.models.enums import StudyStatus
from app.repositories import (
    PlanRepository,
    StudyDayRepository,
    TrackerRepository,
)
from app.schemas.study_day import StudyDayResponse, StudyDayUpdate
from app.schemas.tracker import TrackerResponse, TrackerUpdate


class StudyDayService:
    def __init__(self, db: Session, user_id: int) -> None:
        self.db = db
        self.user_id = user_id
        self.plans = PlanRepository(db)
        self.days = StudyDayRepository(db)
        self.trackers = TrackerRepository(db)

    def get_day(self, plan_id: int, day_number: int) -> StudyDayResponse:
        day = self._require_day_by_number(plan_id, day_number)
        return StudyDayResponse.model_validate(day)

    def update_day(
        self, plan_id: int, day_number: int, payload: StudyDayUpdate
    ) -> StudyDayResponse:
        day = self._require_day_by_number(plan_id, day_number)

        data = payload.model_dump(exclude_unset=True)

        if "status" in data and data["status"] is not None:
            self._apply_status(day, data["status"])

        for field_name in ("notes", "focus", "task", "difficulty"):
            if field_name in data:
                setattr(day, field_name, data[field_name])

        status_changed = "status" in data and data["status"] is not None

        self.db.commit()
        self.db.refresh(day)

        # A status change may complete the plan (all days DONE/SKIPPED) or
        # reopen a completed one. Keep plan.status in sync automatically.
        if status_changed:
            from app.services.plan_service import PlanService

            PlanService(self.db, self.user_id).sync_completion(day.plan_id)

        return StudyDayResponse.model_validate(day)

    def get_tracker(self, study_day_id: int) -> TrackerResponse | None:
        self._require_day(study_day_id)
        tracker = self.trackers.get_by_study_day(study_day_id)
        return TrackerResponse.model_validate(tracker) if tracker else None

    def upsert_tracker(
        self, study_day_id: int, payload: TrackerUpdate
    ) -> TrackerResponse:
        self._require_day(study_day_id)
        tracker = self.trackers.get_by_study_day(study_day_id)
        data = payload.model_dump()

        if tracker is None:
            tracker = DailyTracker(study_day_id=study_day_id, **data)
            self.trackers.add(tracker)
        else:
            for key, value in data.items():
                setattr(tracker, key, value)

        self.db.commit()
        self.db.refresh(tracker)
        return TrackerResponse.model_validate(tracker)

    # -- helpers -------------------------------------------------------------
    @staticmethod
    def _apply_status(day: StudyDay, status: StudyStatus) -> None:
        day.status = status
        if status == StudyStatus.DONE:
            if day.completed_at is None:
                day.completed_at = datetime.now(timezone.utc)
        else:
            day.completed_at = None

    def _require_day(self, study_day_id: int) -> StudyDay:
        day = self.days.get(study_day_id)
        # Verify the day belongs to a plan owned by the current user. We treat
        # a foreign day as "not found" to avoid leaking existence.
        if day is None or self.plans.get(day.plan_id, self.user_id) is None:
            raise NotFoundError(
                f"Study day {study_day_id} not found", code="STUDY_DAY_NOT_FOUND"
            )
        return day

    def _require_day_by_number(self, plan_id: int, day_number: int) -> StudyDay:
        if self.plans.get(plan_id, self.user_id) is None:
            raise NotFoundError(f"Plan {plan_id} not found", code="PLAN_NOT_FOUND")
        day = self.days.get_by_plan_and_day(plan_id, day_number)
        if day is None:
            raise NotFoundError(
                f"Day {day_number} not found in plan {plan_id}",
                code="STUDY_DAY_NOT_FOUND",
            )
        return day
