from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.semester import Semester


class Division(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "divisions"
    __table_args__ = (
        Index(
            "uq_divisions_department_semester_name_lower",
            "department_id",
            "semester_id",
            text("lower(btrim(name))"),
            unique=True,
        ),
        CheckConstraint("student_count >= 1", name="ck_divisions_student_count_positive"),
    )

    name: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "A", "B"
    student_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    semester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True
    )

    department: Mapped["Department"] = relationship(back_populates="divisions")
    semester: Mapped["Semester"] = relationship(back_populates="divisions")

    def __repr__(self) -> str:
        return f"<Division {self.name}>"
