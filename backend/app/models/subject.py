from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.faculty import faculty_subject_association

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.faculty import Faculty
    from app.models.semester import Semester


class Subject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (
        Index("uq_subjects_code_lower", text("lower(btrim(code))"), unique=True),
        CheckConstraint("credits BETWEEN 1 AND 10", name="ck_subjects_credits_range"),
        CheckConstraint("theory_hours_per_week BETWEEN 0 AND 20", name="ck_subjects_theory_hours_range"),
        CheckConstraint("practical_hours_per_week BETWEEN 0 AND 20", name="ck_subjects_practical_hours_range"),
        CheckConstraint(
            "theory_hours_per_week + practical_hours_per_week > 0",
            name="ck_subjects_has_teaching_hours",
        ),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    theory_hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    practical_hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    semester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    semester: Mapped["Semester"] = relationship(back_populates="subjects")
    department: Mapped["Department"] = relationship(back_populates="subjects")
    faculty_members: Mapped[list["Faculty"]] = relationship(
        secondary=faculty_subject_association, back_populates="subjects"
    )

    def __repr__(self) -> str:
        return f"<Subject {self.code}>"
