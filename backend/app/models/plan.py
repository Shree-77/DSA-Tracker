"""Plan ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from app.database import Base
from app.models.enums import PlanStatus

if TYPE_CHECKING:
    from app.models.study_day import StudyDay
    from app.models.user import User


class Plan(Base):
    """A study plan (any subject) created from an imported Excel workbook."""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[PlanStatus] = mapped_column(
        SAEnum(PlanStatus, name="plan_status"),
        nullable=False,
        default=PlanStatus.ACTIVE,
    )
    # Exactly one plan per user may have is_selected=True; that is the plan
    # shown by default ("the current plan") when the app opens. Switching
    # plans just moves this flag; it never deletes or mutates other plans.
    is_selected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    user: Mapped["User"] = relationship(back_populates="plans")

    days: Mapped[List["StudyDay"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="StudyDay.day_number",
    )
