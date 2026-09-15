"""Per-user AI provider settings ORM model.

Stores the user's own LLM API key (e.g. an NVIDIA ``nvapi-...`` key) so the
backend can call the provider on their behalf. The key is *encrypted at rest*
(see ``app.utils.crypto``); the plaintext never touches the database and is
never returned to the client — only a masked preview is exposed.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserAISetting(Base):
    """AI provider configuration for a single user (one row per user)."""

    __tablename__ = "user_ai_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Provider identifier ("nvidia" for now). Kept flexible for future
    # OpenAI-compatible providers without a schema change.
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="nvidia"
    )
    # Fernet-encrypted API key (ciphertext, base64 text). Never plaintext.
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    # Last 4 characters of the plaintext key, stored for a masked UI preview.
    api_key_last4: Mapped[str] = mapped_column(String(8), nullable=False)
    # Chosen model id (NVIDIA NIM model slug).
    model: Mapped[str] = mapped_column(
        String(150), nullable=False, default="meta/llama-3.1-70b-instruct"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=now(),
        onupdate=now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship()
