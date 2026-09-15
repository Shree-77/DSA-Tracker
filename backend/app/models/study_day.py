"""StudyDay ORM model."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from app.database import Base
from app.models.enums import StudyStatus

if TYPE_CHECKING:
    from app.models.daily_tracker import DailyTracker
    from app.models.plan import Plan


class StudyDay(Base):
    """A single day within a plan (Day 1 .. Day N)."""

    __tablename__ = "study_days"
    __table_args__ = (
        UniqueConstraint("plan_id", "day_number", name="uq_study_day_plan_day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )

    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    week_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phase: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    focus: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    task: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    status: Mapped[StudyStatus] = mapped_column(
        SAEnum(StudyStatus, name="study_status"),
        nullable=False,
        default=StudyStatus.NOT_STARTED,
    )

    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=now(),
        onupdate=now(),
        nullable=False,
    )

    plan: Mapped["Plan"] = relationship(back_populates="days")
    tracker: Mapped[Optional["DailyTracker"]] = relationship(
        back_populates="study_day",
        cascade="all, delete-orphan",
        uselist=False,
    )
