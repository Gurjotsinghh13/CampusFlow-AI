from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.academic_year import AcademicYear
    from app.models.division import Division
    from app.models.subject import Subject


class Semester(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "semesters"
    __table_args__ = (
        UniqueConstraint("academic_year_id", "number", name="uq_semester_year_number"),
        CheckConstraint("number BETWEEN 1 AND 12", name="ck_semesters_number_range"),
    )

    number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-8
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True
    )

    academic_year: Mapped["AcademicYear"] = relationship(back_populates="semesters")
    divisions: Mapped[list["Division"]] = relationship(back_populates="semester", cascade="all, delete-orphan")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="semester", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Semester {self.number}>"
