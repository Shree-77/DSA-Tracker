"""Import service: turns a parsed workbook into persisted Plan/StudyDay rows.

Uses a single database transaction. On any validation error the whole import
is rolled back — no partial data is committed.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.exceptions import ImportValidationError
from app.models import DailyTracker, StudyDay
from app.repositories import PlanRepository, StudyDayRepository, TrackerRepository
from app.schemas.plan import (
    ImportPreviewResponse,
    ImportSummary,
    PhaseSummary,
    PlanResponse,
)
from app.utils.excel_parser import ParseResult, parse_workbook


class ImportService:
    def __init__(self, db: Session, user_id: int) -> None:
        self.db = db
        self.user_id = user_id
        self.plans = PlanRepository(db)
        self.days = StudyDayRepository(db)
        self.trackers = TrackerRepository(db)

    # -- Preview (no commit) -------------------------------------------------
    def preview(
        self, content: bytes, start_date: date, plan_name: str | None = None
    ) -> ImportPreviewResponse:
        result = parse_workbook(content, plan_name=plan_name)
        weeks = self._distinct_weeks(result)
        phases = self._phase_summaries(result)
        end_date = self._end_date(start_date, result)

        return ImportPreviewResponse(
            valid=result.valid,
            plan_name=result.plan_name,
            total_days=len(result.days),
            total_weeks=len(weeks),
            total_phases=len(phases),
            phases=phases,
            start_date=start_date if result.days else None,
            end_date=end_date,
            errors=result.errors,
            trackers_detected=len(result.trackers),
        )

    # -- Import (commit or rollback) ----------------------------------------
    def import_plan(
        self, content: bytes, start_date: date, plan_name: str | None = None
    ) -> ImportSummary:
        result = parse_workbook(content, plan_name=plan_name)
        if not result.valid:
            errors = result.errors or ["The uploaded file did not contain any days."]
            raise ImportValidationError(errors)

        try:
            # Each import creates a brand new plan. Users can hold multiple
            # plans at once (e.g. different subjects) and switch between
            # them; the newly imported plan becomes the selected/active one.
            plan = self.plans.create(
                user_id=self.user_id,
                name=result.plan_name,
                description=result.description,
                total_days=len(result.days),
                select_as_active=True,
            )

            day_by_number: dict[int, StudyDay] = {}
            for parsed in result.days:
                scheduled = start_date + timedelta(days=parsed.day_number - 1)
                study_day = StudyDay(
                    plan_id=plan.id,
                    day_number=parsed.day_number,
                    week_number=parsed.week_number,
                    phase=parsed.phase,
                    focus=parsed.focus,
                    task=parsed.task,
                    difficulty=parsed.difficulty,
                    status=parsed.status,
                    scheduled_date=scheduled,
                    notes=parsed.notes,
                )
                self.days.add(study_day)
                day_by_number[parsed.day_number] = study_day

            self.db.flush()  # assign study_day ids

            trackers_imported = 0
            for parsed_tracker in result.trackers:
                study_day = day_by_number.get(parsed_tracker.day_number)
                if study_day is None:
                    continue
                tracker = DailyTracker(
                    study_day_id=study_day.id,
                    study_date=parsed_tracker.study_date,
                    study_hours=parsed_tracker.study_hours,
                    problems_attempted=parsed_tracker.problems_attempted,
                    solved_alone=parsed_tracker.solved_alone,
                    needed_hint=parsed_tracker.needed_hint,
                    needed_solution=parsed_tracker.needed_solution,
                    confidence=parsed_tracker.confidence,
                    reflection=parsed_tracker.reflection,
                )
                self.trackers.add(tracker)
                trackers_imported += 1

            self.db.commit()
        except ImportValidationError:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(plan)

        weeks = self._distinct_weeks(result)
        phases = self._phase_summaries(result)
        end_date = self._end_date(start_date, result)

        return ImportSummary(
            plan=PlanResponse.model_validate(plan),
            total_days=len(result.days),
            total_weeks=len(weeks),
            total_phases=len(phases),
            start_date=start_date,
            end_date=end_date or start_date,
            trackers_imported=trackers_imported,
        )

    # -- helpers -------------------------------------------------------------
    @staticmethod
    def _distinct_weeks(result: ParseResult) -> set[int]:
        return {d.week_number for d in result.days if d.week_number is not None}

    @staticmethod
    def _phase_summaries(result: ParseResult) -> list[PhaseSummary]:
        counts: dict[str, int] = {}
        order: list[str] = []
        for d in result.days:
            name = d.phase or "Unspecified"
            if name not in counts:
                counts[name] = 0
                order.append(name)
            counts[name] += 1
        return [PhaseSummary(name=name, days=counts[name]) for name in order]

    @staticmethod
    def _end_date(start_date: date, result: ParseResult) -> date | None:
        if not result.days:
            return None
        max_day = max(d.day_number for d in result.days)
        return start_date + timedelta(days=max_day - 1)
