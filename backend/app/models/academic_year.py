from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.semester import Semester


class AcademicYear(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "academic_years"
    __table_args__ = (
        Index("uq_academic_years_label_lower", text("lower(btrim(label))"), unique=True),
        Index(
            "uq_academic_years_single_active",
            text("(is_active)"),
            unique=True,
            postgresql_where=text("is_active IS TRUE"),
        ),
        CheckConstraint("label ~ '^[0-9]{4}-[0-9]{4}$'", name="ck_academic_years_label_format"),
        CheckConstraint(
            "CASE WHEN label ~ '^[0-9]{4}-[0-9]{4}$' "
            "THEN substring(label from 6 for 4)::integer = substring(label from 1 for 4)::integer + 1 "
            "ELSE false END",
            name="ck_academic_years_label_consecutive",
        ),
    )

    label: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # e.g. "2025-2026"
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    semesters: Mapped[list["Semester"]] = relationship(back_populates="academic_year", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AcademicYear {self.label}>"
