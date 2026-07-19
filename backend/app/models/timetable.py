from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, CheckConstraint, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.division import Division
    from app.models.faculty import Faculty
    from app.models.room import Room
    from app.models.subject import Subject


class GenerationStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    INFEASIBLE = "INFEASIBLE"
    FAILED = "FAILED"


class GeneratedTimetable(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generated_timetables"
    __table_args__ = (
        CheckConstraint(
            "academic_year_label ~ '^[0-9]{4}-[0-9]{4}$'",
            name="ck_generated_timetables_academic_year_label_format",
        ),
        CheckConstraint(
            "CASE WHEN academic_year_label ~ '^[0-9]{4}-[0-9]{4}$' "
            "THEN substring(academic_year_label from 6 for 4)::integer = "
            "substring(academic_year_label from 1 for 4)::integer + 1 "
            "ELSE false END",
            name="ck_generated_timetables_academic_year_label_consecutive",
        ),
        CheckConstraint("cardinality(working_days) BETWEEN 1 AND 7", name="ck_generated_timetables_working_days_count"),
        CheckConstraint(
            "COALESCE(cardinality(array_positions(working_days, 'MONDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'TUESDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'WEDNESDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'THURSDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'FRIDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'SATURDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'SUNDAY')), 0) <= 1",
            name="ck_generated_timetables_working_days_unique",
        ),
        CheckConstraint(
            "working_days <@ ARRAY['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY']::varchar[]",
            name="ck_generated_timetables_working_days_allowed",
        ),
        CheckConstraint("periods_per_day BETWEEN 1 AND 20", name="ck_generated_timetables_periods_range"),
        CheckConstraint(
            "theory_duration_minutes BETWEEN 15 AND 180",
            name="ck_generated_timetables_theory_duration_range",
        ),
        CheckConstraint(
            "practical_duration_minutes BETWEEN 30 AND 300",
            name="ck_generated_timetables_practical_duration_range",
        ),
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False, index=True
    )
    academic_year_label: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, name="generation_status_enum"), nullable=False, default=GenerationStatus.PENDING
    )
    solver_wall_time_seconds: Mapped[float] = mapped_column(nullable=True)
    objective_value: Mapped[float] = mapped_column(nullable=True)
    message: Mapped[str] = mapped_column(String(500), nullable=True)
    working_days: Mapped[list[str]] = mapped_column(ARRAY(String(10)), nullable=False)
    periods_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    theory_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    practical_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    entries: Mapped[list["TimetableEntry"]] = relationship(back_populates="timetable", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GeneratedTimetable {self.id} {self.status}>"


class TimetableEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "timetable_entries"
    __table_args__ = (
        CheckConstraint(
            "day IN ('MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY')",
            name="ck_timetable_entries_day_allowed",
        ),
        CheckConstraint("period_index >= 0", name="ck_timetable_entries_period_index_nonnegative"),
        CheckConstraint("session_type IN ('THEORY','PRACTICAL')", name="ck_timetable_entries_session_type_allowed"),
    )

    timetable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generated_timetables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    division_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("divisions.id"), nullable=False, index=True
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False, index=True
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("faculty.id"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False, index=True
    )

    day: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    period_index: Mapped[int] = mapped_column(Integer, nullable=False)
    session_type: Mapped[str] = mapped_column(String(10), nullable=False)  # THEORY | PRACTICAL
    division_name: Mapped[str] = mapped_column(String(20), nullable=False)
    subject_name: Mapped[str] = mapped_column(String(150), nullable=False)
    subject_code: Mapped[str] = mapped_column(String(20), nullable=False)
    faculty_name: Mapped[str] = mapped_column(String(150), nullable=False)
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)

    timetable: Mapped["GeneratedTimetable"] = relationship(back_populates="entries")
    division: Mapped["Division"] = relationship(viewonly=True)
    subject: Mapped["Subject"] = relationship(viewonly=True)
    faculty: Mapped["Faculty"] = relationship(viewonly=True)
    room: Mapped["Room"] = relationship(viewonly=True)

    def __repr__(self) -> str:
        return f"<TimetableEntry {self.day} P{self.period_index}>"
