"""Excel import tests: valid, missing columns, invalid rows, duplicates, rollback."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select

from app.exceptions import ImportValidationError
from app.models import Plan, StudyDay
from app.services import ImportService
from tests import fixtures

START = date(2026, 9, 15)


def test_import_valid_workbook_creates_56_days(db_session, test_user_id):
    content = fixtures.build_valid_workbook()
    summary = ImportService(db_session, test_user_id).import_plan(content, START)

    assert summary.total_days == 56
    assert summary.total_weeks == 8
    assert summary.total_phases == 8
    assert summary.start_date == START
    assert summary.end_date == date(2026, 11, 9)  # day 56
    assert summary.trackers_imported == 2

    days = db_session.execute(select(StudyDay).order_by(StudyDay.day_number)).scalars().all()
    assert len(days) == 56
    assert days[0].day_number == 1
    assert days[0].scheduled_date == START
    assert days[7].phase == "Recursive Sorting"  # Day 8
    assert days[7].focus == "Bubble Sort"
    assert days[7].difficulty == "Easy"


def test_import_preview_does_not_commit(db_session, test_user_id):
    content = fixtures.build_valid_workbook()
    preview = ImportService(db_session, test_user_id).preview(content, START)

    assert preview.valid is True
    assert preview.total_days == 56
    assert preview.total_weeks == 8
    assert preview.total_phases == 8
    assert preview.end_date == date(2026, 11, 9)
    # Nothing persisted.
    assert db_session.execute(select(Plan)).scalars().first() is None


def test_missing_columns_raise_import_error(db_session, test_user_id):
    content = fixtures.build_workbook_missing_columns()
    with pytest.raises(ImportValidationError) as exc:
        ImportService(db_session, test_user_id).import_plan(content, START)
    assert any("Day" in e for e in exc.value.details["errors"])


def test_invalid_row_reports_missing_day(db_session, test_user_id):
    content = fixtures.build_workbook_invalid_row()
    with pytest.raises(ImportValidationError) as exc:
        ImportService(db_session, test_user_id).import_plan(content, START)
    errors = exc.value.details["errors"]
    assert any("Day number is missing" in e for e in errors)


def test_duplicate_days_rejected(db_session, test_user_id):
    content = fixtures.build_workbook_duplicate_days()
    with pytest.raises(ImportValidationError) as exc:
        ImportService(db_session, test_user_id).import_plan(content, START)
    assert any("Duplicate day number" in e for e in exc.value.details["errors"])


def test_invalid_difficulty_rejected(db_session, test_user_id):
    content = fixtures.build_workbook_invalid_difficulty()
    with pytest.raises(ImportValidationError) as exc:
        ImportService(db_session, test_user_id).import_plan(content, START)
    assert any("Invalid difficulty" in e for e in exc.value.details["errors"])


def test_reimport_creates_second_plan_and_selects_it(db_session, test_user_id):
    """A second import adds a new plan alongside the first and selects it.

    Users can hold multiple plans; importing again must not delete history.
    """
    content = fixtures.build_valid_workbook()
    first = ImportService(db_session, test_user_id).import_plan(content, START)
    second = ImportService(db_session, test_user_id).import_plan(content, START)

    plans = db_session.execute(select(Plan)).scalars().all()
    assert len(plans) == 2
    assert {p.id for p in plans} == {first.plan.id, second.plan.id}

    # Both plans' days must still exist (56 each).
    days = db_session.execute(select(StudyDay)).scalars().all()
    assert len(days) == 112

    # The most recently imported plan becomes the selected/active one.
    selected = [p for p in plans if p.is_selected]
    assert len(selected) == 1
    assert selected[0].id == second.plan.id


def test_failed_import_rolls_back_completely(db_session, test_user_id):
    content = fixtures.build_workbook_invalid_row()
    with pytest.raises(ImportValidationError):
        ImportService(db_session, test_user_id).import_plan(content, START)
    # No plan and no days should exist after rollback.
    assert db_session.execute(select(Plan)).scalars().first() is None
    assert db_session.execute(select(StudyDay)).scalars().first() is None
