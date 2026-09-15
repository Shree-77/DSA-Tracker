"""Plan ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from app.database import Base

if TYPE_CHECKING:
    from app.models.study_day import StudyDay


class Plan(Base):
    """A DSA preparation plan created from an imported Excel workbook."""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=now(),
        onupdate=now(),
        nullable=False,
    )

    days: Mapped[List["StudyDay"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="StudyDay.day_number",
    )
