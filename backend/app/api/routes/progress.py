"""Progress routes (scoped to the authenticated user)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.progress import ProgressResponse
from app.services import ProgressService

router = APIRouter(prefix="/plans", tags=["progress"])


@router.get("/{plan_id}/progress", response_model=ProgressResponse)
def get_progress(
    plan_id: int,
    today: date | None = Query(default=None, description="Override for testing."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProgressResponse:
    return ProgressService(db, current_user.id).get_progress(plan_id, today)
