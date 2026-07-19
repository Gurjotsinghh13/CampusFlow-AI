"""add time and day value check constraints

Revision ID: 20260719_0011
Revises: 20260719_0010
Create Date: 2026-07-19 00:11:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0011"
down_revision: str | None = "20260719_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ALLOWED_DAYS_ARRAY = "ARRAY['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY']::varchar[]"
TIME_FORMAT_RE = "'^([01][0-9]|2[0-3]):[0-5][0-9]$'"


def _raise_if_exists(table: str, condition: str, message: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM {table} WHERE {condition}) THEN
                RAISE EXCEPTION '{message}';
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    _raise_if_exists(
        "constraints",
        f"NOT (working_days <@ {ALLOWED_DAYS_ARRAY})",
        "Scheduling constraints contain invalid working days",
    )
    for column in ("college_start_time", "college_end_time", "lunch_break_start", "lunch_break_end"):
        _raise_if_exists(
            "constraints",
            f"NOT ({column} ~ {TIME_FORMAT_RE})",
            f"Scheduling constraints contain invalid {column}",
        )
    _raise_if_exists(
        "generated_timetables",
        "cardinality(working_days) < 1 OR cardinality(working_days) > 7",
        "Generated timetable contains invalid working day count",
    )
    _raise_if_exists(
        "generated_timetables",
        f"NOT (working_days <@ {ALLOWED_DAYS_ARRAY})",
        "Generated timetable contains invalid working days",
    )
    _raise_if_exists(
        "generated_timetables",
        "periods_per_day < 1 OR periods_per_day > 20",
        "Generated timetable contains invalid periods_per_day",
    )
    _raise_if_exists(
        "generated_timetables",
        "theory_duration_minutes < 15 OR theory_duration_minutes > 180",
        "Generated timetable contains invalid theory duration",
    )
    _raise_if_exists(
        "generated_timetables",
        "practical_duration_minutes < 30 OR practical_duration_minutes > 300",
        "Generated timetable contains invalid practical duration",
    )
    _raise_if_exists(
        "timetable_entries",
        "day NOT IN ('MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY')",
        "Timetable entry contains invalid day",
    )
    _raise_if_exists(
        "timetable_entries",
        "period_index < 0",
        "Timetable entry contains negative period_index",
    )
    _raise_if_exists(
        "timetable_entries",
        "session_type NOT IN ('THEORY','PRACTICAL')",
        "Timetable entry contains invalid session_type",
    )

    op.create_check_constraint(
        "ck_constraints_working_days_allowed",
        "constraints",
        f"working_days <@ {ALLOWED_DAYS_ARRAY}",
    )
    op.create_check_constraint(
        "ck_constraints_college_start_time_format",
        "constraints",
        f"college_start_time ~ {TIME_FORMAT_RE}",
    )
    op.create_check_constraint(
        "ck_constraints_college_end_time_format",
        "constraints",
        f"college_end_time ~ {TIME_FORMAT_RE}",
    )
    op.create_check_constraint(
        "ck_constraints_lunch_break_start_format",
        "constraints",
        f"lunch_break_start ~ {TIME_FORMAT_RE}",
    )
    op.create_check_constraint(
        "ck_constraints_lunch_break_end_format",
        "constraints",
        f"lunch_break_end ~ {TIME_FORMAT_RE}",
    )
    op.create_check_constraint(
        "ck_generated_timetables_working_days_count",
        "generated_timetables",
        "cardinality(working_days) BETWEEN 1 AND 7",
    )
    op.create_check_constraint(
        "ck_generated_timetables_working_days_allowed",
        "generated_timetables",
        f"working_days <@ {ALLOWED_DAYS_ARRAY}",
    )
    op.create_check_constraint(
        "ck_generated_timetables_periods_range",
        "generated_timetables",
        "periods_per_day BETWEEN 1 AND 20",
    )
    op.create_check_constraint(
        "ck_generated_timetables_theory_duration_range",
        "generated_timetables",
        "theory_duration_minutes BETWEEN 15 AND 180",
    )
    op.create_check_constraint(
        "ck_generated_timetables_practical_duration_range",
        "generated_timetables",
        "practical_duration_minutes BETWEEN 30 AND 300",
    )
    op.create_check_constraint(
        "ck_timetable_entries_day_allowed",
        "timetable_entries",
        "day IN ('MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY')",
    )
    op.create_check_constraint(
        "ck_timetable_entries_period_index_nonnegative",
        "timetable_entries",
        "period_index >= 0",
    )
    op.create_check_constraint(
        "ck_timetable_entries_session_type_allowed",
        "timetable_entries",
        "session_type IN ('THEORY','PRACTICAL')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_timetable_entries_session_type_allowed", "timetable_entries", type_="check")
    op.drop_constraint("ck_timetable_entries_period_index_nonnegative", "timetable_entries", type_="check")
    op.drop_constraint("ck_timetable_entries_day_allowed", "timetable_entries", type_="check")
    op.drop_constraint("ck_generated_timetables_practical_duration_range", "generated_timetables", type_="check")
    op.drop_constraint("ck_generated_timetables_theory_duration_range", "generated_timetables", type_="check")
    op.drop_constraint("ck_generated_timetables_periods_range", "generated_timetables", type_="check")
    op.drop_constraint("ck_generated_timetables_working_days_allowed", "generated_timetables", type_="check")
    op.drop_constraint("ck_generated_timetables_working_days_count", "generated_timetables", type_="check")
    op.drop_constraint("ck_constraints_lunch_break_end_format", "constraints", type_="check")
    op.drop_constraint("ck_constraints_lunch_break_start_format", "constraints", type_="check")
    op.drop_constraint("ck_constraints_college_end_time_format", "constraints", type_="check")
    op.drop_constraint("ck_constraints_college_start_time_format", "constraints", type_="check")
    op.drop_constraint("ck_constraints_working_days_allowed", "constraints", type_="check")
