"""initial schema

Revision ID: 20260719_0001
Revises:
Create Date: 2026-07-19 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    room_type_enum = postgresql.ENUM(
    "CLASSROOM",
    "LAB",
    name="room_type_enum",
    create_type=False
    )

    generation_status_enum = postgresql.ENUM(
    "PENDING",
    "RUNNING",
    "SUCCESS",
    "INFEASIBLE",
    "FAILED",
    name="generation_status_enum",
    create_type=False
    )
    room_type_enum.create(op.get_bind(), checkfirst=True)
    generation_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "academic_years",
        sa.Column("label", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_academic_years_label"), "academic_years", ["label"], unique=True)

    op.create_table(
        "constraints",
        sa.Column("working_days", postgresql.ARRAY(sa.String(length=10)), nullable=False),
        sa.Column("college_start_time", sa.String(length=5), nullable=False),
        sa.Column("college_end_time", sa.String(length=5), nullable=False),
        sa.Column("lunch_break_start", sa.String(length=5), nullable=False),
        sa.Column("lunch_break_end", sa.String(length=5), nullable=False),
        sa.Column("number_of_periods", sa.Integer(), nullable=False),
        sa.Column("theory_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("practical_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )

    op.create_table(
        "departments",
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_departments_code"), "departments", ["code"], unique=True)
    op.create_index(op.f("ix_departments_name"), "departments", ["name"], unique=True)

    op.create_table(
        "rooms",
        sa.Column("room_number", sa.String(length=20), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("room_type", room_type_enum, nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_room_number"), "rooms", ["room_number"], unique=True)

    op.create_table(
        "faculty",
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("employee_id", sa.String(length=30), nullable=False),
        sa.Column("max_daily_lectures", sa.Integer(), nullable=False),
        sa.Column("max_weekly_lectures", sa.Integer(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_faculty_department_id"), "faculty", ["department_id"], unique=False)
    op.create_index(op.f("ix_faculty_employee_id"), "faculty", ["employee_id"], unique=True)

    op.create_table(
        "generated_timetables",
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", generation_status_enum, nullable=False),
        sa.Column("solver_wall_time_seconds", sa.Float(), nullable=True),
        sa.Column("objective_value", sa.Float(), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("working_days", postgresql.ARRAY(sa.String(length=10)), nullable=False),
        sa.Column("periods_per_day", sa.Integer(), nullable=False),
        sa.Column("theory_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("practical_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_generated_timetables_academic_year_id"), "generated_timetables", ["academic_year_id"], unique=False)

    op.create_table(
        "semesters",
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academic_year_id", "number", name="uq_semester_year_number"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_semesters_academic_year_id"), "semesters", ["academic_year_id"], unique=False)

    op.create_table(
        "divisions",
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("student_count", sa.Integer(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("semester_id", "name", name="uq_division_semester_name"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_divisions_department_id"), "divisions", ["department_id"], unique=False)
    op.create_index(op.f("ix_divisions_semester_id"), "divisions", ["semester_id"], unique=False)

    op.create_table(
        "subjects",
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("theory_hours_per_week", sa.Integer(), nullable=False),
        sa.Column("practical_hours_per_week", sa.Integer(), nullable=False),
        sa.Column("semester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_subject_code"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_subjects_code"), "subjects", ["code"], unique=False)
    op.create_index(op.f("ix_subjects_department_id"), "subjects", ["department_id"], unique=False)
    op.create_index(op.f("ix_subjects_semester_id"), "subjects", ["semester_id"], unique=False)

    op.create_table(
        "faculty_subjects",
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("faculty_id", "subject_id"),
    )

    op.create_table(
        "timetable_entries",
        sa.Column("timetable_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("division_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day", sa.String(length=10), nullable=False),
        sa.Column("period_index", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.String(length=10), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["division_id"], ["divisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timetable_id"], ["generated_timetables.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_timetable_entries_day"), "timetable_entries", ["day"], unique=False)
    op.create_index(op.f("ix_timetable_entries_division_id"), "timetable_entries", ["division_id"], unique=False)
    op.create_index(op.f("ix_timetable_entries_faculty_id"), "timetable_entries", ["faculty_id"], unique=False)
    op.create_index(op.f("ix_timetable_entries_room_id"), "timetable_entries", ["room_id"], unique=False)
    op.create_index(op.f("ix_timetable_entries_subject_id"), "timetable_entries", ["subject_id"], unique=False)
    op.create_index(op.f("ix_timetable_entries_timetable_id"), "timetable_entries", ["timetable_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_timetable_entries_timetable_id"), table_name="timetable_entries")
    op.drop_index(op.f("ix_timetable_entries_subject_id"), table_name="timetable_entries")
    op.drop_index(op.f("ix_timetable_entries_room_id"), table_name="timetable_entries")
    op.drop_index(op.f("ix_timetable_entries_faculty_id"), table_name="timetable_entries")
    op.drop_index(op.f("ix_timetable_entries_division_id"), table_name="timetable_entries")
    op.drop_index(op.f("ix_timetable_entries_day"), table_name="timetable_entries")
    op.drop_table("timetable_entries")
    op.drop_table("faculty_subjects")
    op.drop_index(op.f("ix_subjects_semester_id"), table_name="subjects")
    op.drop_index(op.f("ix_subjects_department_id"), table_name="subjects")
    op.drop_index(op.f("ix_subjects_code"), table_name="subjects")
    op.drop_table("subjects")
    op.drop_index(op.f("ix_divisions_semester_id"), table_name="divisions")
    op.drop_index(op.f("ix_divisions_department_id"), table_name="divisions")
    op.drop_table("divisions")
    op.drop_index(op.f("ix_semesters_academic_year_id"), table_name="semesters")
    op.drop_table("semesters")
    op.drop_index(op.f("ix_generated_timetables_academic_year_id"), table_name="generated_timetables")
    op.drop_table("generated_timetables")
    op.drop_index(op.f("ix_faculty_employee_id"), table_name="faculty")
    op.drop_index(op.f("ix_faculty_department_id"), table_name="faculty")
    op.drop_table("faculty")
    op.drop_index(op.f("ix_rooms_room_number"), table_name="rooms")
    op.drop_table("rooms")
    op.drop_index(op.f("ix_departments_name"), table_name="departments")
    op.drop_index(op.f("ix_departments_code"), table_name="departments")
    op.drop_table("departments")
    op.drop_table("constraints")
    op.drop_index(op.f("ix_academic_years_label"), table_name="academic_years")
    op.drop_table("academic_years")
    postgresql.ENUM(name="generation_status_enum").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="room_type_enum").drop(op.get_bind(), checkfirst=True)
