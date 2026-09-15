"""Data-access for UserAISetting (one row per user)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_settings import UserAISetting


class AISettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_user(self, user_id: int) -> UserAISetting | None:
        stmt = select(UserAISetting).where(UserAISetting.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        user_id: int,
        *,
        provider: str,
        api_key_encrypted: str,
        api_key_last4: str,
        model: str,
    ) -> UserAISetting:
        existing = self.get_for_user(user_id)
        if existing is None:
            existing = UserAISetting(user_id=user_id)
            self.db.add(existing)
        existing.provider = provider
        existing.api_key_encrypted = api_key_encrypted
        existing.api_key_last4 = api_key_last4
        existing.model = model
        self.db.flush()
        return existing

    def delete_for_user(self, user_id: int) -> bool:
        existing = self.get_for_user(user_id)
        if existing is None:
            return False
        self.db.delete(existing)
        self.db.flush()
        return True
