"""AI service: study-plan chat, structured generation, and import.

Responsibilities:
  * Persist/read the user's provider API key (encrypted at rest).
  * Call the OpenAI-compatible NVIDIA NIM endpoint on the user's behalf.
  * Drive the two-step flow: (1) conversational planning, (2) convert the
    agreed plan into strict JSON, which is turned into an .xlsx and handed to
    the existing ImportService for validated persistence.

No provider secret is ever returned to the client — only a masked preview.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import AppError, ValidationAppError
from app.repositories.ai_settings_repository import AISettingsRepository
from app.schemas.ai import (
    AISettingsResponse,
    AISettingsUpdate,
    ChatMessage,
    ChatResponse,
    GeneratedPlan,
)
from app.schemas.plan import ImportSummary
from app.services.import_service import ImportService
from app.utils.crypto import InvalidToken, decrypt_secret, encrypt_secret
from app.utils.excel_builder import build_plan_workbook

logger = logging.getLogger("dsa_tracker.ai")


class AIConfigError(AppError):
    """Raised when the user has not configured a usable API key."""

    code = "AI_NOT_CONFIGURED"
    status_code = 400
    message = "No AI API key is configured. Add one in Settings first."


class AIProviderError(AppError):
    """Raised when the upstream LLM provider fails or returns bad data."""

    code = "AI_PROVIDER_ERROR"
    status_code = 502
    message = "The AI provider could not be reached."


# System prompt for the conversational planning phase.
_PLANNER_SYSTEM_PROMPT = (
    "You are StudyPlanGPT, an expert study-plan creator. Your ONLY job is to "
    "help the user design a realistic, day-by-day study plan for whatever "
    "subject they want (programming, exams, languages, music — anything).\n\n"
    "Guidelines:\n"
    "- Ask a brief clarifying question ONLY if the request is too vague to "
    "plan (e.g. missing subject, duration, or level). Otherwise, propose a "
    "plan directly.\n"
    "- Present plans grouped into phases/weeks with a clear daily focus and a "
    "concrete task per day. Keep tasks specific and achievable in one day.\n"
    "- Use difficulty labels Easy / Medium / Hard / Mixed.\n"
    "- Be concise and well-structured (use headings and lists). Do NOT output "
    "JSON in this phase — write for a human. End by asking the user to confirm "
    "or request changes."
)

# System prompt for the strict JSON conversion phase.
_JSON_SYSTEM_PROMPT = (
    "You convert an agreed study plan into STRICT JSON. Output ONLY a single "
    "JSON object, no markdown, no commentary, no code fences.\n\n"
    "Schema:\n"
    "{\n"
    '  "name": string,               // short plan title\n'
    '  "description": string,        // one-sentence summary\n'
    '  "total_days": number,\n'
    '  "days": [\n'
    "    {\n"
    '      "day": number,            // 1-based, sequential, no gaps\n'
    '      "week": number,\n'
    '      "phase": string,\n'
    '      "focus": string,\n'
    '      "task": string,           // the concrete task/problems for the day\n'
    '      "difficulty": "Easy"|"Medium"|"Hard"|"Mixed",\n'
    '      "notes": string           // may be empty\n'
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Rules: days MUST be numbered 1..total_days with no gaps or duplicates. "
    "total_days MUST equal the length of days. Every day MUST have a task."
)


class AIService:
    def __init__(self, db: Session, user_id: int) -> None:
        self.db = db
        self.user_id = user_id
        self.repo = AISettingsRepository(db)

    # -- Settings -----------------------------------------------------------
    def get_settings(self) -> AISettingsResponse:
        row = self.repo.get_for_user(self.user_id)
        if row is None:
            return AISettingsResponse(configured=False)
        return AISettingsResponse(
            configured=True,
            provider=row.provider,
            model=row.model,
            api_key_preview=self._mask(row.api_key_last4),
        )

    def save_settings(self, payload: AISettingsUpdate) -> AISettingsResponse:
        api_key = payload.api_key.strip()
        if not api_key:
            raise ValidationAppError("API key must not be empty.")

        model = (payload.model or "").strip() or settings.ai_default_model
        row = self.repo.upsert(
            self.user_id,
            provider=payload.provider.strip().lower() or "nvidia",
            api_key_encrypted=encrypt_secret(api_key),
            api_key_last4=api_key[-4:],
            model=model,
        )
        self.db.commit()
        self.db.refresh(row)
        return AISettingsResponse(
            configured=True,
            provider=row.provider,
            model=row.model,
            api_key_preview=self._mask(row.api_key_last4),
        )

    def delete_settings(self) -> None:
        self.repo.delete_for_user(self.user_id)
        self.db.commit()

    # -- Chat ---------------------------------------------------------------
    def chat(self, message: str, history: list[ChatMessage]) -> ChatResponse:
        api_key, model = self._resolve_credentials()
        messages = [{"role": "system", "content": _PLANNER_SYSTEM_PROMPT}]
        messages += [{"role": m.role, "content": m.content} for m in history]
        messages.append({"role": "user", "content": message})

        reply = self._chat_completion(api_key, model, messages, temperature=0.7)
        return ChatResponse(reply=reply, model=model)

    # -- Structured generation ---------------------------------------------
    def generate_plan(
        self, conversation: list[ChatMessage], instruction: str | None
    ) -> GeneratedPlan:
        api_key, model = self._resolve_credentials()

        convo_text = "\n".join(f"{m.role.upper()}: {m.content}" for m in conversation)
        user_content = (
            "Convert the study plan agreed in this conversation into the JSON "
            "schema exactly.\n\n=== CONVERSATION ===\n" + convo_text
        )
        if instruction:
            user_content += f"\n\n=== FINAL ADJUSTMENT ===\n{instruction}"

        messages = [
            {"role": "system", "content": _JSON_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        raw = self._chat_completion(
            api_key, model, messages, temperature=0.2, json_mode=True
        )
        data = self._parse_json_object(raw)
        return self._validate_generated_plan(data)

    # -- Confirm & import ---------------------------------------------------
    def confirm_import(
        self, plan: GeneratedPlan, start_date: date
    ) -> ImportSummary:
        """Turn a confirmed structured plan into a real, persisted plan."""
        workbook = build_plan_workbook(plan.model_dump())
        # Reuse the exact validated import pipeline used for manual uploads.
        return ImportService(self.db, self.user_id).import_plan(
            workbook, start_date, plan_name=plan.name
        )

    # -- helpers ------------------------------------------------------------
    def _resolve_credentials(self) -> tuple[str, str]:
        row = self.repo.get_for_user(self.user_id)
        if row is None:
            raise AIConfigError()
        try:
            api_key = decrypt_secret(row.api_key_encrypted)
        except InvalidToken as exc:  # key rotated or corrupted
            raise AIConfigError(
                "Stored API key could not be read; please re-enter it in Settings.",
                code="AI_KEY_UNREADABLE",
            ) from exc
        return api_key, row.model

    def _chat_completion(
        self,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        json_mode: bool = False,
    ) -> str:
        url = f"{settings.ai_base_url.rstrip('/')}/chat/completions"
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
            "stream": False,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=settings.ai_request_timeout) as client:
                resp = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=body,
                )
        except httpx.HTTPError as exc:
            logger.warning("AI request failed: %s", exc)
            raise AIProviderError() from exc

        if resp.status_code in (401, 403):
            raise AIConfigError(
                "The AI provider rejected your API key. Check it in Settings.",
                code="AI_KEY_INVALID",
                status_code=400,
            )
        if resp.status_code == 429:
            raise AIProviderError(
                "The AI provider is rate-limiting requests. Try again shortly.",
                code="AI_RATE_LIMITED",
                status_code=429,
            )
        if resp.status_code >= 400:
            logger.warning("AI provider %s: %s", resp.status_code, resp.text[:500])
            raise AIProviderError(
                "The AI provider returned an error.",
                details={"status": resp.status_code},
            )

        try:
            payload = resp.json()
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise AIProviderError("Malformed response from AI provider.") from exc

        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("The AI returned an empty response.")
        return content.strip()

    @staticmethod
    def _parse_json_object(raw: str) -> dict[str, Any]:
        text = raw.strip()
        # Strip accidental code fences if the model added them.
        if text.startswith("```"):
            text = text.strip("`")
            if text.lstrip().lower().startswith("json"):
                text = text.lstrip()[4:]
        # Isolate the outermost JSON object.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIProviderError(
                "The AI did not return valid JSON. Try generating again."
            ) from exc
        if not isinstance(data, dict):
            raise AIProviderError("The AI returned JSON of an unexpected shape.")
        return data

    @staticmethod
    def _validate_generated_plan(data: dict[str, Any]) -> GeneratedPlan:
        days = data.get("days")
        if not isinstance(days, list) or not days:
            raise AIProviderError("The generated plan contained no days.")
        if len(days) > settings.ai_max_days:
            raise ValidationAppError(
                f"Generated plan has too many days (max {settings.ai_max_days}).",
                code="AI_PLAN_TOO_LARGE",
            )
        # Keep total_days consistent with the actual list length.
        data.setdefault("name", "AI Study Plan")
        data["total_days"] = len(days)
        try:
            return GeneratedPlan.model_validate(data)
        except Exception as exc:  # noqa: BLE001 - surface as provider error
            raise AIProviderError(
                "The generated plan did not match the expected structure."
            ) from exc

    @staticmethod
    def _mask(last4: str) -> str:
        return f"****{last4}" if last4 else "****"
