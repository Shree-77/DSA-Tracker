"""DailyTracker ORM model."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from app.database import Base

if TYPE_CHECKING:
    from app.models.study_day import StudyDay


class DailyTracker(Base):
    """Per-day tracking metrics (time, problems, confidence, reflection)."""

    __tablename__ = "daily_trackers"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 1 AND confidence <= 5)",
            name="ck_daily_tracker_confidence_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_day_id: Mapped[int] = mapped_column(
        ForeignKey("study_days.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    study_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    study_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    problems_attempted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    solved_alone: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    needed_hint: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    needed_solution: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reflection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=now(),
        onupdate=now(),
        nullable=False,
    )

    study_day: Mapped["StudyDay"] = relationship(back_populates="tracker")
