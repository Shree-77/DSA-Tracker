"""Plan-related routes.

Route handlers stay thin: they parse input and delegate to services. No
database logic lives here. Every route is scoped to the authenticated user.
"""

from __future__ import annotations

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.exceptions import ValidationAppError
from app.models import User
from app.models.enums import PlanStatus
from app.schemas.plan import (
    ImportPreviewResponse,
    ImportSummary,
    PlanResponse,
    PlanSelectResponse,
)
from app.schemas.study_day import StudyDayResponse, TodayResponse
from app.services import ImportService, PlanService

router = APIRouter(prefix="/plans", tags=["plans"])

_ALLOWED_EXTENSIONS = (".xlsx", ".xlsm")


def _validate_upload(file: UploadFile) -> None:
    name = (file.filename or "").lower()
    if not name.endswith(_ALLOWED_EXTENSIONS):
        raise ValidationAppError(
            "Only .xlsx Excel files are supported.",
            code="INVALID_FILE_TYPE",
            details={"filename": file.filename},
        )


@router.post("/import", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
async def import_plan(
    start_date: date = Form(..., description="Date mapped to Day 1."),
    file: UploadFile = File(...),
    plan_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportSummary:
    _validate_upload(file)
    content = await file.read()
    return ImportService(db, current_user.id).import_plan(content, start_date, plan_name)


@router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_import(
    start_date: date = Form(...),
    file: UploadFile = File(...),
    plan_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportPreviewResponse:
    _validate_upload(file)
    content = await file.read()
    return ImportService(db, current_user.id).preview(content, start_date, plan_name)


@router.get("", response_model=List[PlanResponse])
def list_plans(
    status: PlanStatus | None = Query(
        default=None, description="Filter plans by lifecycle status."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PlanResponse]:
    return PlanService(db, current_user.id).list_plans(status=status)


@router.get("/history", response_model=List[PlanResponse])
def plan_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PlanResponse]:
    """Plans the user has completed, most recently completed first."""
    return PlanService(db, current_user.id).history()


@router.post("/{plan_id}/select", response_model=PlanSelectResponse)
def select_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanSelectResponse:
    """Switch the user's current/active plan (non-destructive)."""
    plan = PlanService(db, current_user.id).select_plan(plan_id)
    return PlanSelectResponse(plan=plan)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanResponse:
    return PlanService(db, current_user.id).get_plan(plan_id)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    PlanService(db, current_user.id).delete_plan(plan_id)


@router.get("/{plan_id}/days", response_model=List[StudyDayResponse])
def list_days(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[StudyDayResponse]:
    return PlanService(db, current_user.id).list_days(plan_id)


@router.get("/{plan_id}/today", response_model=TodayResponse)
def get_today(
    plan_id: int,
    today: date | None = Query(default=None, description="Override for testing."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TodayResponse:
    return PlanService(db, current_user.id).get_today(plan_id, today)
