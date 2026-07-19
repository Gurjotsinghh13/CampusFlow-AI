from __future__ import annotations

from sqlalchemy import ARRAY, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Constraint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "constraints"
    __table_args__ = (
        CheckConstraint("cardinality(working_days) BETWEEN 1 AND 7", name="ck_constraints_working_days_count"),
        CheckConstraint(
            "COALESCE(cardinality(array_positions(working_days, 'MONDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'TUESDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'WEDNESDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'THURSDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'FRIDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'SATURDAY')), 0) <= 1 AND "
            "COALESCE(cardinality(array_positions(working_days, 'SUNDAY')), 0) <= 1",
            name="ck_constraints_working_days_unique",
        ),
        CheckConstraint(
            "working_days <@ ARRAY['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY']::varchar[]",
            name="ck_constraints_working_days_allowed",
        ),
        CheckConstraint("number_of_periods BETWEEN 1 AND 20", name="ck_constraints_periods_range"),
        CheckConstraint("theory_duration_minutes BETWEEN 15 AND 180", name="ck_constraints_theory_duration_range"),
        CheckConstraint(
            "practical_duration_minutes BETWEEN 30 AND 300",
            name="ck_constraints_practical_duration_range",
        ),
        CheckConstraint(
            "college_start_time ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="ck_constraints_college_start_time_format",
        ),
        CheckConstraint(
            "college_end_time ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="ck_constraints_college_end_time_format",
        ),
        CheckConstraint(
            "lunch_break_start ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="ck_constraints_lunch_break_start_format",
        ),
        CheckConstraint(
            "lunch_break_end ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'",
            name="ck_constraints_lunch_break_end_format",
        ),
        CheckConstraint("college_start_time < college_end_time", name="ck_constraints_college_time_order"),
        CheckConstraint("lunch_break_start < lunch_break_end", name="ck_constraints_lunch_time_order"),
        CheckConstraint(
            "college_start_time <= lunch_break_start AND lunch_break_end <= college_end_time",
            name="ck_constraints_lunch_within_college_hours",
        ),
    )

    working_days: Mapped[list[str]] = mapped_column(ARRAY(String(10)), nullable=False)
    college_start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "09:00"
    college_end_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "17:00"
    lunch_break_start: Mapped[str] = mapped_column(String(5), nullable=False)
    lunch_break_end: Mapped[str] = mapped_column(String(5), nullable=False)
    number_of_periods: Mapped[int] = mapped_column(Integer, nullable=False)
    theory_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    practical_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)

    def __repr__(self) -> str:
        return "<Constraint config>"
