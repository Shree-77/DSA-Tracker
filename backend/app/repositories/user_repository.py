"""Data-access for User."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        """Case-insensitive username lookup to enforce uniqueness robustly."""
        stmt = select(User).where(func.lower(User.username) == username.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, username: str, password_hash: str) -> User:
        user = User(username=username, password_hash=password_hash)
        self.db.add(user)
        self.db.flush()  # populate user.id without committing
        return user
