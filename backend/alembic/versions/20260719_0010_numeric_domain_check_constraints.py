"""add numeric domain check constraints

Revision ID: 20260719_0010
Revises: 20260719_0009
Create Date: 2026-07-19 00:10:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0010"
down_revision: str | None = "20260719_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


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
    _raise_if_exists("semesters", "number < 1 OR number > 12", "Invalid semester number exists")
    _raise_if_exists("rooms", "capacity < 1 OR capacity > 1000", "Invalid room capacity exists")
    _raise_if_exists(
        "faculty",
        "max_daily_lectures < 1 OR max_daily_lectures > 12",
        "Invalid faculty daily lecture limit exists",
    )
    _raise_if_exists(
        "faculty",
        "max_weekly_lectures < 1 OR max_weekly_lectures > 60",
        "Invalid faculty weekly lecture limit exists",
    )
    _raise_if_exists("subjects", "credits < 1 OR credits > 10", "Invalid subject credit value exists")
    _raise_if_exists(
        "subjects",
        "theory_hours_per_week < 0 OR theory_hours_per_week > 20",
        "Invalid subject theory hours exist",
    )
    _raise_if_exists(
        "subjects",
        "practical_hours_per_week < 0 OR practical_hours_per_week > 20",
        "Invalid subject practical hours exist",
    )
    _raise_if_exists(
        "subjects",
        "theory_hours_per_week + practical_hours_per_week <= 0",
        "Subject without teaching hours exists",
    )
    _raise_if_exists(
        "constraints",
        "cardinality(working_days) < 1 OR cardinality(working_days) > 7",
        "Invalid working day count exists",
    )
    _raise_if_exists(
        "constraints",
        "number_of_periods < 1 OR number_of_periods > 20",
        "Invalid number_of_periods exists",
    )
    _raise_if_exists(
        "constraints",
        "theory_duration_minutes < 15 OR theory_duration_minutes > 180",
        "Invalid theory duration exists",
    )
    _raise_if_exists(
        "constraints",
        "practical_duration_minutes < 30 OR practical_duration_minutes > 300",
        "Invalid practical duration exists",
    )
    _raise_if_exists(
        "constraints",
        "college_start_time >= college_end_time",
        "Invalid college time ordering exists",
    )
    _raise_if_exists(
        "constraints",
        "lunch_break_start >= lunch_break_end",
        "Invalid lunch time ordering exists",
    )
    _raise_if_exists(
        "constraints",
        "college_start_time > lunch_break_start OR lunch_break_end > college_end_time",
        "Lunch break outside college hours exists",
    )

    op.create_check_constraint("ck_semesters_number_range", "semesters", "number BETWEEN 1 AND 12")
    op.create_check_constraint("ck_rooms_capacity_range", "rooms", "capacity BETWEEN 1 AND 1000")
    op.create_check_constraint(
        "ck_faculty_max_daily_lectures_range",
        "faculty",
        "max_daily_lectures BETWEEN 1 AND 12",
    )
    op.create_check_constraint(
        "ck_faculty_max_weekly_lectures_range",
        "faculty",
        "max_weekly_lectures BETWEEN 1 AND 60",
    )
    op.create_check_constraint("ck_subjects_credits_range", "subjects", "credits BETWEEN 1 AND 10")
    op.create_check_constraint(
        "ck_subjects_theory_hours_range",
        "subjects",
        "theory_hours_per_week BETWEEN 0 AND 20",
    )
    op.create_check_constraint(
        "ck_subjects_practical_hours_range",
        "subjects",
        "practical_hours_per_week BETWEEN 0 AND 20",
    )
    op.create_check_constraint(
        "ck_subjects_has_teaching_hours",
        "subjects",
        "theory_hours_per_week + practical_hours_per_week > 0",
    )
    op.create_check_constraint(
        "ck_constraints_working_days_count",
        "constraints",
        "cardinality(working_days) BETWEEN 1 AND 7",
    )
    op.create_check_constraint(
        "ck_constraints_periods_range",
        "constraints",
        "number_of_periods BETWEEN 1 AND 20",
    )
    op.create_check_constraint(
        "ck_constraints_theory_duration_range",
        "constraints",
        "theory_duration_minutes BETWEEN 15 AND 180",
    )
    op.create_check_constraint(
        "ck_constraints_practical_duration_range",
        "constraints",
        "practical_duration_minutes BETWEEN 30 AND 300",
    )
    op.create_check_constraint(
        "ck_constraints_college_time_order",
        "constraints",
        "college_start_time < college_end_time",
    )
    op.create_check_constraint(
        "ck_constraints_lunch_time_order",
        "constraints",
        "lunch_break_start < lunch_break_end",
    )
    op.create_check_constraint(
        "ck_constraints_lunch_within_college_hours",
        "constraints",
        "college_start_time <= lunch_break_start AND lunch_break_end <= college_end_time",
    )


def downgrade() -> None:
    op.drop_constraint("ck_constraints_lunch_within_college_hours", "constraints", type_="check")
    op.drop_constraint("ck_constraints_lunch_time_order", "constraints", type_="check")
    op.drop_constraint("ck_constraints_college_time_order", "constraints", type_="check")
    op.drop_constraint("ck_constraints_practical_duration_range", "constraints", type_="check")
    op.drop_constraint("ck_constraints_theory_duration_range", "constraints", type_="check")
    op.drop_constraint("ck_constraints_periods_range", "constraints", type_="check")
    op.drop_constraint("ck_constraints_working_days_count", "constraints", type_="check")
    op.drop_constraint("ck_subjects_has_teaching_hours", "subjects", type_="check")
    op.drop_constraint("ck_subjects_practical_hours_range", "subjects", type_="check")
    op.drop_constraint("ck_subjects_theory_hours_range", "subjects", type_="check")
    op.drop_constraint("ck_subjects_credits_range", "subjects", type_="check")
    op.drop_constraint("ck_faculty_max_weekly_lectures_range", "faculty", type_="check")
    op.drop_constraint("ck_faculty_max_daily_lectures_range", "faculty", type_="check")
    op.drop_constraint("ck_rooms_capacity_range", "rooms", type_="check")
    op.drop_constraint("ck_semesters_number_range", "semesters", type_="check")
