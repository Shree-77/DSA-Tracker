"""Initial schema: plans, study_days, daily_trackers.

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

study_status = sa.Enum(
    "NOT_STARTED",
    "IN_PROGRESS",
    "DONE",
    "SKIPPED",
    name="study_status",
)


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_days", sa.Integer(), nullable=False, server_default="0"),
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
    )

    op.create_table(
        "study_days",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=True),
        sa.Column("phase", sa.String(length=255), nullable=True),
        sa.Column("focus", sa.String(length=255), nullable=True),
        sa.Column("task", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(length=50), nullable=True),
        sa.Column("status", study_status, nullable=False, server_default="NOT_STARTED"),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "plan_id", "day_number", name="uq_study_day_plan_day"
        ),
    )
    op.create_index(
        "ix_study_days_plan_id", "study_days", ["plan_id"], unique=False
    )

    op.create_table(
        "daily_trackers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_day_id", sa.Integer(), nullable=False),
        sa.Column("study_date", sa.Date(), nullable=True),
        sa.Column("study_hours", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "problems_attempted", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("solved_alone", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("needed_hint", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "needed_solution", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("reflection", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["study_day_id"], ["study_days.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("study_day_id"),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 1 AND confidence <= 5)",
            name="ck_daily_tracker_confidence_range",
        ),
    )
    op.create_index(
        "ix_daily_trackers_study_day_id",
        "daily_trackers",
        ["study_day_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_daily_trackers_study_day_id", table_name="daily_trackers")
    op.drop_table("daily_trackers")
    op.drop_index("ix_study_days_plan_id", table_name="study_days")
    op.drop_table("study_days")
    op.drop_table("plans")
    study_status.drop(op.get_bind(), checkfirst=True)
