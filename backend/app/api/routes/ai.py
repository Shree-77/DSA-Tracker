"""AI study-plan routes.

Endpoints (all scoped to the authenticated user):
  * GET    /ai/settings          -> current AI config (masked, never the key)
  * PUT    /ai/settings          -> save/replace the provider API key
  * DELETE /ai/settings          -> remove the stored key
  * POST   /ai/chat              -> conversational plan design
  * POST   /ai/generate         -> convert the agreed plan to structured JSON
  * POST   /ai/confirm          -> import a confirmed plan (creates a real plan)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.ai import (
    AISettingsResponse,
    AISettingsUpdate,
    ChatRequest,
    ChatResponse,
    ConfirmImportRequest,
    ConfirmImportResponse,
    GeneratePlanRequest,
    GeneratedPlan,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/settings", response_model=AISettingsResponse)
def get_ai_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsResponse:
    return AIService(db, current_user.id).get_settings()


@router.put("/settings", response_model=AISettingsResponse)
def save_ai_settings(
    payload: AISettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsResponse:
    return AIService(db, current_user.id).save_settings(payload)


@router.delete("/settings", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    AIService(db, current_user.id).delete_settings()


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    return AIService(db, current_user.id).chat(payload.message, payload.history)


@router.post("/generate", response_model=GeneratedPlan)
def generate_plan(
    payload: GeneratePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedPlan:
    return AIService(db, current_user.id).generate_plan(
        payload.conversation, payload.instruction
    )


@router.post(
    "/confirm",
    response_model=ConfirmImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_import(
    payload: ConfirmImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConfirmImportResponse:
    summary = AIService(db, current_user.id).confirm_import(
        payload.plan, payload.start_date
    )
    return ConfirmImportResponse(summary=summary)
