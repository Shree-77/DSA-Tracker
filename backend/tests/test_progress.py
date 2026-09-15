"""Progress + streak tests."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import StudyStatus
from app.schemas.study_day import StudyDayUpdate
from app.schemas.tracker import TrackerUpdate
from app.services import ImportService, ProgressService, StudyDayService
from app.repositories import StudyDayRepository
from tests import fixtures

START = date(2026, 9, 15)


@pytest.fixture()
def plan_id(db_session) -> int:
    summary = ImportService(db_session).import_plan(fixtures.build_valid_workbook(), START)
    return summary.plan.id


def test_completion_percentage(db_session, plan_id):
    days_service = StudyDayService(db_session)
    for day_number in range(1, 8):  # 7 of 56 -> 12.5%
        days_service.update_day(plan_id, day_number, StudyDayUpdate(status=StudyStatus.DONE))

    progress = ProgressService(db_session).get_progress(plan_id, today=START + timedelta(days=6))
    assert progress.total_days == 56
    assert progress.completed_days == 7
    assert progress.remaining_days == 49
    assert progress.completion_percentage == 12.5


def test_current_and_longest_streak(db_session, plan_id):
    service = StudyDayService(db_session)
    # Complete days 1..5 (scheduled Sep 15..19). "today" = Sep 19.
    for day_number in range(1, 6):
        service.update_day(plan_id, day_number, StudyDayUpdate(status=StudyStatus.DONE))

    today = START + timedelta(days=4)  # Sep 19
    progress = ProgressService(db_session).get_progress(plan_id, today=today)
    assert progress.current_streak == 5
    assert progress.longest_streak == 5


def test_incomplete_today_does_not_break_streak(db_session, plan_id):
    service = StudyDayService(db_session)
    # Complete days 1..4 (Sep 15..18). Day 5 (Sep 19) not done. today = Sep 19.
    for day_number in range(1, 5):
        service.update_day(plan_id, day_number, StudyDayUpdate(status=StudyStatus.DONE))

    today = START + timedelta(days=4)  # Sep 19, day 5 still open
    progress = ProgressService(db_session).get_progress(plan_id, today=today)
    # Streak anchored at yesterday since today isn't complete yet.
    assert progress.current_streak == 4


def test_broken_streak(db_session, plan_id):
    service = StudyDayService(db_session)
    # Complete days 1,2 and 4 (skip day 3). today = day 4.
    for day_number in (1, 2, 4):
        service.update_day(plan_id, day_number, StudyDayUpdate(status=StudyStatus.DONE))

    today = START + timedelta(days=3)  # day 4
    progress = ProgressService(db_session).get_progress(plan_id, today=today)
    assert progress.current_streak == 1  # only day 4
    assert progress.longest_streak == 2  # days 1-2


def test_statistics_aggregation(db_session, plan_id):
    day_repo = StudyDayRepository(db_session)
    service = StudyDayService(db_session)

    d1 = day_repo.get_by_plan_and_day(plan_id, 1)
    d2 = day_repo.get_by_plan_and_day(plan_id, 2)
    service.upsert_tracker(
        d1.id,
        TrackerUpdate(study_hours=2.0, problems_attempted=3, solved_alone=2, needed_hint=1, confidence=4),
    )
    service.upsert_tracker(
        d2.id,
        TrackerUpdate(study_hours=1.5, problems_attempted=2, solved_alone=2, needed_solution=0, confidence=5),
    )

    progress = ProgressService(db_session).get_progress(plan_id, today=START)
    assert progress.total_study_hours == 3.5
    assert progress.problems_attempted == 5
    assert progress.solved_alone == 4
    assert progress.needed_hint == 1
    assert progress.average_confidence == 4.5


def test_weekly_breakdown(db_session, plan_id):
    service = StudyDayService(db_session)
    for day_number in range(1, 8):  # complete all of week 1
        service.update_day(plan_id, day_number, StudyDayUpdate(status=StudyStatus.DONE))

    progress = ProgressService(db_session).get_progress(plan_id, today=START + timedelta(days=6))
    week1 = next(w for w in progress.weekly if w.week_number == 1)
    assert week1.total == 7
    assert week1.completed == 7
    week2 = next(w for w in progress.weekly if w.week_number == 2)
    assert week2.completed == 0
