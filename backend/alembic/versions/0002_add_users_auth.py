"""Add users table and user_id ownership on plans.

Existing plans (single-user era) are migrated to a placeholder account so the
new NOT NULL foreign key can be applied without data loss. That account has an
unusable password hash; the operator can reassign or delete those plans later.

Revision ID: 0002_add_users_auth
Revises: 0001_initial
Create Date: 2025-01-02 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_users_auth"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# bcrypt hash that no password can produce -> the account cannot be logged into.
_UNUSABLE_HASH = "!disabled-legacy-account"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # Add user_id as nullable first so existing rows survive.
    op.add_column("plans", sa.Column("user_id", sa.Integer(), nullable=True))

    # Backfill: if there are legacy plans, create a placeholder owner for them.
    bind = op.get_bind()
    legacy_count = bind.execute(
        sa.text("SELECT COUNT(*) FROM plans WHERE user_id IS NULL")
    ).scalar()
    if legacy_count and legacy_count > 0:
        legacy_user_id = bind.execute(
            sa.text(
                "INSERT INTO users (username, password_hash) "
                "VALUES (:u, :p) RETURNING id"
            ).bindparams(u="legacy", p=_UNUSABLE_HASH)
        ).scalar()
        bind.execute(
            sa.text("UPDATE plans SET user_id = :uid WHERE user_id IS NULL")
            .bindparams(uid=legacy_user_id)
        )

    # Enforce NOT NULL + FK + index now that every row has an owner.
    op.alter_column("plans", "user_id", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_plans_user_id", "plans", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_plans_user_id_users",
        "plans",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_plans_user_id_users", "plans", type_="foreignkey")
    op.drop_index("ix_plans_user_id", table_name="plans")
    op.drop_column("plans", "user_id")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
