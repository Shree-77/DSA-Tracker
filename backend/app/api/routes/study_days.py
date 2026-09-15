"""Study day + tracker routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.study_day import StudyDayResponse, StudyDayUpdate
from app.schemas.tracker import TrackerResponse, TrackerUpdate
from app.services import StudyDayService

router = APIRouter(tags=["study-days"])


@router.get(
    "/plans/{plan_id}/days/{day_number}", response_model=StudyDayResponse
)
def get_day(
    plan_id: int, day_number: int, db: Session = Depends(get_db)
) -> StudyDayResponse:
    return StudyDayService(db).get_day(plan_id, day_number)


@router.patch(
    "/plans/{plan_id}/days/{day_number}", response_model=StudyDayResponse
)
def update_day(
    plan_id: int,
    day_number: int,
    payload: StudyDayUpdate,
    db: Session = Depends(get_db),
) -> StudyDayResponse:
    return StudyDayService(db).update_day(plan_id, day_number, payload)


@router.get(
    "/study-days/{study_day_id}/tracker",
    responses={204: {"description": "No tracker recorded yet."}},
)
def get_tracker(study_day_id: int, db: Session = Depends(get_db)):
    tracker = StudyDayService(db).get_tracker(study_day_id)
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
) -> TrackerResponse:
    return StudyDayService(db).upsert_tracker(study_day_id, payload)
