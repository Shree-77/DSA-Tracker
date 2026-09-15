"""Add plan status, is_selected (active plan pointer), and completed_at.

Every existing plan is set to ACTIVE. For each user, their most recently
created plan becomes ``is_selected = true`` so behaviour is unchanged for
existing installs (this mirrors the old "most recent plan" default).

Revision ID: 0003_plan_status_and_selection
Revises: 0002_add_users_auth
Create Date: 2025-01-03 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_plan_status_and_selection"
down_revision: str | None = "0002_add_users_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

plan_status = sa.Enum("ACTIVE", "COMPLETED", "ARCHIVED", name="plan_status")


def upgrade() -> None:
    bind = op.get_bind()
    plan_status.create(bind, checkfirst=True)

    op.add_column(
        "plans",
        sa.Column(
            "status", plan_status, nullable=False, server_default="ACTIVE"
        ),
    )
    op.add_column(
        "plans",
        sa.Column(
            "is_selected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "plans", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Backfill: mark each user's most recently created plan as selected so
    # existing users keep seeing the same plan they saw before this change.
    # Written as a portable correlated subquery (works on Postgres and
    # SQLite) rather than DISTINCT ON, which SQLite does not support.
    op.execute(
        """
        UPDATE plans
        SET is_selected = TRUE
        WHERE id IN (
            SELECT p1.id
            FROM plans p1
            WHERE p1.created_at = (
                SELECT MAX(p2.created_at)
                FROM plans p2
                WHERE p2.user_id = p1.user_id
            )
        )
        """
    )

    op.create_index(
        "ix_plans_user_id_is_selected",
        "plans",
        ["user_id", "is_selected"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_plans_user_id_is_selected", table_name="plans")
    op.drop_column("plans", "completed_at")
    op.drop_column("plans", "is_selected")
    op.drop_column("plans", "status")
    plan_status.drop(op.get_bind(), checkfirst=True)
</content>
