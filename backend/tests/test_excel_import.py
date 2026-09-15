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


def test_import_valid_workbook_creates_56_days(db_session):
    content = fixtures.build_valid_workbook()
    summary = ImportService(db_session).import_plan(content, START)

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


def test_import_preview_does_not_commit(db_session):
    content = fixtures.build_valid_workbook()
    preview = ImportService(db_session).preview(content, START)

    assert preview.valid is True
    assert preview.total_days == 56
    assert preview.total_weeks == 8
    assert preview.total_phases == 8
    assert preview.end_date == date(2026, 11, 9)
    # Nothing persisted.
    assert db_session.execute(select(Plan)).scalars().first() is None


def test_missing_columns_raise_import_error(db_session):
    content = fixtures.build_workbook_missing_columns()
    with pytest.raises(ImportValidationError) as exc:
        ImportService(db_session).import_plan(content, START)
    assert any("Day" in e for e in exc.value.details["errors"])


def test_invalid_row_reports_missing_day(db_session):
    content = fixtures.build_workbook_invalid_row()
    with pytest.raises(ImportValidationError) as exc:
        ImportService(db_session).import_plan(content, START)
    errors = exc.value.details["errors"]
    assert any("Day number is missing" in e for e in errors)


def test_duplicate_days_rejected(db_session):
    content = fixtures.build_workbook_duplicate_days()
    with pytest.raises(ImportValidationError) as exc:
        ImportService(db_session).import_plan(content, START)
    assert any("Duplicate day number" in e for e in exc.value.details["errors"])


def test_invalid_difficulty_rejected(db_session):
    content = fixtures.build_workbook_invalid_difficulty()
    with pytest.raises(ImportValidationError) as exc:
        ImportService(db_session).import_plan(content, START)
    assert any("Invalid difficulty" in e for e in exc.value.details["errors"])


def test_reimport_replaces_existing_plan(db_session):
    """A second import replaces the first plan instead of accumulating."""
    content = fixtures.build_valid_workbook()
    first = ImportService(db_session).import_plan(content, START)
    second = ImportService(db_session).import_plan(content, START)

    plans = db_session.execute(select(Plan)).scalars().all()
    assert len(plans) == 1
    assert plans[0].id == second.plan.id
    assert plans[0].id != first.plan.id

    # Old plan's days must be gone (only the new plan's days remain).
    days = db_session.execute(select(StudyDay)).scalars().all()
    assert all(d.plan_id == second.plan.id for d in days)
    assert len(days) == 56


def test_failed_import_rolls_back_completely(db_session):
    content = fixtures.build_workbook_invalid_row()
    with pytest.raises(ImportValidationError):
        ImportService(db_session).import_plan(content, START)
    # No plan and no days should exist after rollback.
    assert db_session.execute(select(Plan)).scalars().first() is None
    assert db_session.execute(select(StudyDay)).scalars().first() is None
