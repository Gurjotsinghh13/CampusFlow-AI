from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, String, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.subject import Subject

faculty_subject_association = Table(
    "faculty_subjects",
    Base.metadata,
    Column("faculty_id", UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="CASCADE"), primary_key=True),
    Column("subject_id", UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True),
)


class Faculty(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "faculty"
    __table_args__ = (
        Index("uq_faculty_employee_id_lower", text("lower(btrim(employee_id))"), unique=True),
        CheckConstraint("max_daily_lectures BETWEEN 1 AND 12", name="ck_faculty_max_daily_lectures_range"),
        CheckConstraint("max_weekly_lectures BETWEEN 1 AND 60", name="ck_faculty_max_weekly_lectures_range"),
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    max_daily_lectures: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    max_weekly_lectures: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    department: Mapped["Department"] = relationship(back_populates="faculty")
    subjects: Mapped[list["Subject"]] = relationship(
        secondary=faculty_subject_association, back_populates="faculty_members"
    )

    def __repr__(self) -> str:
        return f"<Faculty {self.employee_id}>"
