"""Study day + tracker service tests."""

from __future__ import annotations

from datetime import date

import pytest

from app.exceptions import NotFoundError
from app.models.enums import StudyStatus
from app.repositories import StudyDayRepository
from app.schemas.study_day import StudyDayUpdate
from app.schemas.tracker import TrackerUpdate
from app.services import ImportService, StudyDayService
from tests import fixtures

START = date(2026, 9, 15)


@pytest.fixture()
def plan_id(db_session, test_user_id) -> int:
    summary = ImportService(db_session, test_user_id).import_plan(fixtures.build_valid_workbook(), START)
    return summary.plan.id


def test_mark_day_done_sets_completed_at(db_session, plan_id, test_user_id):
    service = StudyDayService(db_session, test_user_id)
    result = service.update_day(plan_id, 8, StudyDayUpdate(status=StudyStatus.DONE))
    assert result.status == StudyStatus.DONE
    assert result.completed_at is not None


def test_mark_in_progress_clears_completed_at(db_session, plan_id, test_user_id):
    service = StudyDayService(db_session, test_user_id)
    service.update_day(plan_id, 8, StudyDayUpdate(status=StudyStatus.DONE))
    result = service.update_day(plan_id, 8, StudyDayUpdate(status=StudyStatus.IN_PROGRESS))
    assert result.status == StudyStatus.IN_PROGRESS
    assert result.completed_at is None


def test_update_notes(db_session, plan_id, test_user_id):
    service = StudyDayService(db_session, test_user_id)
    result = service.update_day(plan_id, 3, StudyDayUpdate(notes="Revisit tail recursion"))
    assert result.notes == "Revisit tail recursion"


def test_upsert_tracker_creates_and_updates(db_session, plan_id, test_user_id):
    day = StudyDayRepository(db_session).get_by_plan_and_day(plan_id, 8)
    service = StudyDayService(db_session, test_user_id)

    created = service.upsert_tracker(
        day.id,
        TrackerUpdate(
            study_hours=2.0,
            problems_attempted=3,
            solved_alone=2,
            needed_hint=1,
            confidence=4,
            reflection="Learned bubble sort recursion",
        ),
    )
    assert created.study_hours == 2.0
    assert created.confidence == 4

    updated = service.upsert_tracker(day.id, TrackerUpdate(study_hours=3.5, confidence=5))
    assert updated.id == created.id  # same row (upsert)
    assert updated.study_hours == 3.5
    assert updated.confidence == 5


def test_missing_plan_raises(db_session, test_user_id):
    with pytest.raises(NotFoundError):
        StudyDayService(db_session, test_user_id).get_day(9999, 1)


def test_missing_day_raises(db_session, plan_id, test_user_id):
    with pytest.raises(NotFoundError):
        StudyDayService(db_session, test_user_id).get_day(plan_id, 999)
