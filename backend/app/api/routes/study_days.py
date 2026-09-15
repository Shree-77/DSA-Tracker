"""Study day + tracker routes (scoped to the authenticated user)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.study_day import StudyDayResponse, StudyDayUpdate
from app.schemas.tracker import TrackerResponse, TrackerUpdate
from app.services import StudyDayService

router = APIRouter(tags=["study-days"])


@router.get(
    "/plans/{plan_id}/days/{day_number}", response_model=StudyDayResponse
)
def get_day(
    plan_id: int,
    day_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudyDayResponse:
    return StudyDayService(db, current_user.id).get_day(plan_id, day_number)


@router.patch(
    "/plans/{plan_id}/days/{day_number}", response_model=StudyDayResponse
)
def update_day(
    plan_id: int,
    day_number: int,
    payload: StudyDayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudyDayResponse:
    return StudyDayService(db, current_user.id).update_day(plan_id, day_number, payload)


@router.get(
    "/study-days/{study_day_id}/tracker",
    responses={204: {"description": "No tracker recorded yet."}},
)
def get_tracker(
    study_day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tracker = StudyDayService(db, current_user.id).get_tracker(study_day_id)
    if tracker is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return tracker


@router.put(
    "/study-days/{study_day_id}/tracker", response_model=TrackerResponse
)
def upsert_tracker(
    study_day_id: int,
    payload: TrackerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TrackerResponse:
    return StudyDayService(db, current_user.id).upsert_tracker(study_day_id, payload)
