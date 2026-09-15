"""Tests for the AI study-plan feature.

Provider HTTP calls are mocked (no real network / no real API key needed).
Covers: crypto round-trip, JSON->xlsx->parser bridge, settings persistence
(masked, never plaintext), chat, structured generation, and confirm-import.
"""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import patch

import pytest

from app.schemas.ai import AISettingsUpdate, ChatMessage, GeneratedPlan
from app.services.ai_service import AIConfigError, AIProviderError, AIService
from app.utils.crypto import decrypt_secret, encrypt_secret
from app.utils.excel_builder import build_plan_workbook
from app.utils.excel_parser import parse_workbook


# -- crypto -----------------------------------------------------------------
def test_crypto_round_trip():
    secret = "nvapi-super-secret-key-1234"
    assert decrypt_secret(encrypt_secret(secret)) == secret


def test_ciphertext_is_not_plaintext():
    secret = "nvapi-abcdefghij"
    assert secret not in encrypt_secret(secret)


# -- excel bridge -----------------------------------------------------------
def test_builder_produces_parseable_workbook():
    plan = {
        "name": "Python in 3 Days",
        "description": "Quick intro",
        "days": [
            {"day": 1, "week": 1, "phase": "Basics", "focus": "Syntax",
             "task": "Variables", "difficulty": "easy"},
            {"day": 2, "week": 1, "phase": "Basics", "focus": "Loops",
             "task": "For/while", "difficulty": "MEDIUM"},
            {"day": 3, "week": 1, "phase": "Basics", "focus": "Functions",
             "task": "def & args", "difficulty": "Hard"},
        ],
    }
    result = parse_workbook(build_plan_workbook(plan))
    assert result.valid, result.errors
    assert len(result.days) == 3
    assert result.plan_name == "Python in 3 Days"
    assert result.days[0].difficulty == "Easy"  # normalised
    assert result.days[1].difficulty == "Medium"


# -- settings ---------------------------------------------------------------
def test_save_and_get_settings_masks_key(db_session, test_user_id):
    svc = AIService(db_session, test_user_id)
    assert svc.get_settings().configured is False

    resp = svc.save_settings(
        AISettingsUpdate(api_key="nvapi-1234567890abcd", model="meta/llama")
    )
    assert resp.configured is True
    assert resp.api_key_preview == "****abcd"
    # Plaintext key must never appear in the response.
    assert "nvapi-1234567890abcd" not in json.dumps(resp.model_dump())

    fetched = svc.get_settings()
    assert fetched.configured is True
    assert fetched.model == "meta/llama"
    assert fetched.api_key_preview == "****abcd"


def test_delete_settings(db_session, test_user_id):
    svc = AIService(db_session, test_user_id)
    svc.save_settings(AISettingsUpdate(api_key="nvapi-abcdefgh"))
    svc.delete_settings()
    assert svc.get_settings().configured is False


def test_chat_requires_configured_key(db_session, test_user_id):
    svc = AIService(db_session, test_user_id)
    with pytest.raises(AIConfigError):
        svc.chat("hi", [])


# -- chat & generate (mocked provider) --------------------------------------
def _configured_service(db_session, test_user_id) -> AIService:
    svc = AIService(db_session, test_user_id)
    svc.save_settings(AISettingsUpdate(api_key="nvapi-testkey123"))
    return svc


def test_chat_returns_reply(db_session, test_user_id):
    svc = _configured_service(db_session, test_user_id)
    with patch.object(
        AIService, "_chat_completion", return_value="Here is a plan..."
    ):
        resp = svc.chat("Make me a Python plan", [])
    assert resp.reply == "Here is a plan..."


def test_generate_plan_parses_json(db_session, test_user_id):
    svc = _configured_service(db_session, test_user_id)
    ai_json = json.dumps({
        "name": "2-Day Plan",
        "description": "test",
        "total_days": 2,
        "days": [
            {"day": 1, "week": 1, "phase": "P", "focus": "F",
             "task": "T1", "difficulty": "Easy", "notes": ""},
            {"day": 2, "week": 1, "phase": "P", "focus": "F",
             "task": "T2", "difficulty": "Hard", "notes": ""},
        ],
    })
    with patch.object(AIService, "_chat_completion", return_value=ai_json):
        plan = svc.generate_plan(
            [ChatMessage(role="user", content="python plan")], None
        )
    assert isinstance(plan, GeneratedPlan)
    assert plan.total_days == 2
    assert len(plan.days) == 2


def test_generate_plan_rejects_bad_json(db_session, test_user_id):
    svc = _configured_service(db_session, test_user_id)
    with patch.object(AIService, "_chat_completion", return_value="not json"):
        with pytest.raises(AIProviderError):
            svc.generate_plan(
                [ChatMessage(role="user", content="x")], None
            )


def test_confirm_import_creates_plan(db_session, test_user_id):
    svc = _configured_service(db_session, test_user_id)
    plan = GeneratedPlan.model_validate({
        "name": "Imported AI Plan",
        "description": "d",
        "total_days": 2,
        "days": [
            {"day": 1, "task": "T1", "difficulty": "Easy"},
            {"day": 2, "task": "T2", "difficulty": "Medium"},
        ],
    })
    summary = svc.confirm_import(plan, date(2026, 1, 1))
    assert summary.plan.name == "Imported AI Plan"
    assert summary.total_days == 2
    assert summary.plan.is_selected is True
