"""add case-insensitive unique indexes

Revision ID: 20260719_0004
Revises: 20260719_0003
Create Date: 2026-07-19 00:04:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0004"
down_revision: str | None = "20260719_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _raise_if_case_duplicates_exist(table: str, column: str, label: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT lower(btrim({column}))
                FROM {table}
                GROUP BY lower(btrim({column}))
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot add normalized unique index: duplicate {label} values exist';
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    _raise_if_case_duplicates_exist("academic_years", "label", "academic year label")
    _raise_if_case_duplicates_exist("departments", "code", "department code")
    _raise_if_case_duplicates_exist("departments", "name", "department name")
    _raise_if_case_duplicates_exist("rooms", "room_number", "room number")
    _raise_if_case_duplicates_exist("faculty", "employee_id", "faculty employee ID")
    _raise_if_case_duplicates_exist("subjects", "code", "subject code")

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_academic_years_label_lower "
        "ON academic_years (lower(btrim(label)))"
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_departments_code_lower ON departments (lower(btrim(code)))")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_departments_name_lower ON departments (lower(btrim(name)))")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_rooms_room_number_lower ON rooms (lower(btrim(room_number)))")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_faculty_employee_id_lower ON faculty (lower(btrim(employee_id)))")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_subjects_code_lower ON subjects (lower(btrim(code)))")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_subjects_code_lower")
    op.execute("DROP INDEX IF EXISTS uq_faculty_employee_id_lower")
    op.execute("DROP INDEX IF EXISTS uq_rooms_room_number_lower")
    op.execute("DROP INDEX IF EXISTS uq_departments_name_lower")
    op.execute("DROP INDEX IF EXISTS uq_departments_code_lower")
    op.execute("DROP INDEX IF EXISTS uq_academic_years_label_lower")
