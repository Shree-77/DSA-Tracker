"""User ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from app.database import Base

if TYPE_CHECKING:
    from app.models.plan import Plan


class User(Base):
    """An application user. Usernames are unique (case-insensitive at the
    service layer, enforced unique at the column level)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(150), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=now(),
        onupdate=now(),
        nullable=False,
    )

    plans: Mapped[List["Plan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
