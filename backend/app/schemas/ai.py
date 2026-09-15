"""Schemas for the AI plan-generation feature."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.plan import ImportSummary


# -- Settings ---------------------------------------------------------------
class AISettingsUpdate(BaseModel):
    """Payload to save/replace the user's provider API key."""

    api_key: str = Field(..., min_length=8, max_length=400)
    provider: str = Field(default="nvidia", max_length=50)
    model: str | None = Field(default=None, max_length=150)


class AISettingsResponse(BaseModel):
    """Non-secret view of the user's AI settings (never returns the key)."""

    model_config = ConfigDict(from_attributes=True)

    configured: bool
    provider: str | None = None
    model: str | None = None
    api_key_preview: str | None = Field(
        default=None, description="Masked preview, e.g. 'nvapi-****a1b2'."
    )


# -- Chat -------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    """A user turn plus prior conversation for context."""

    message: str = Field(..., min_length=1, max_length=8000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    reply: str
    model: str


# -- Structured plan generation --------------------------------------------
class GeneratePlanRequest(BaseModel):
    """Ask the AI to convert the agreed-upon plan into structured rows.

    ``conversation`` is the full chat so far so the model has the plan it just
    proposed in context.
    """

    conversation: list[ChatMessage] = Field(..., min_length=1, max_length=30)
    instruction: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional final tweak, e.g. 'make it 8 weeks'.",
    )


class GeneratedDay(BaseModel):
    day: int
    week: int | None = None
    phase: str | None = None
    focus: str | None = None
    task: str | None = None
    difficulty: str | None = None
    notes: str | None = None


class GeneratedPlan(BaseModel):
    """The AI's structured plan, previewed before the user confirms import."""

    name: str
    description: str | None = None
    total_days: int
    days: list[GeneratedDay]


# -- Confirm & import -------------------------------------------------------
class ConfirmImportRequest(BaseModel):
    """User confirms a previously-generated plan and imports it."""

    plan: GeneratedPlan
    start_date: date = Field(..., description="Date mapped to Day 1.")


class ConfirmImportResponse(BaseModel):
    summary: ImportSummary
