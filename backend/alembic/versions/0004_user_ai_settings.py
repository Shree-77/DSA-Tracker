"""Add user_ai_settings table for per-user AI provider keys.

Stores the user's own LLM API key encrypted at rest (Fernet). One row per
user, enforced by a unique constraint on user_id.

Revision ID: 0004_user_ai_settings
Revises: 0003_plan_status_and_selection
Create Date: 2025-01-04 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_user_ai_settings"
down_revision: str | None = "0003_plan_status_and_selection"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_ai_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False,
            server_default="nvidia",
        ),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("api_key_last4", sa.String(length=8), nullable=False),
        sa.Column(
            "model",
            sa.String(length=150),
            nullable=False,
            server_default="meta/llama-3.1-70b-instruct",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("user_id", name="uq_user_ai_settings_user_id"),
    )
    op.create_index(
        "ix_user_ai_settings_user_id",
        "user_ai_settings",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_user_ai_settings_user_id", table_name="user_ai_settings")
    op.drop_table("user_ai_settings")
