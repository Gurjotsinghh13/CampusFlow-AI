"""remove redundant case-sensitive unique constraints

Revision ID: 20260719_0015
Revises: 20260719_0014
Create Date: 2026-07-19 00:15:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0015"
down_revision: str | None = "20260719_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _replace_unique_index_with_plain_index(index_name: str, table_name: str, columns: list[str]) -> None:
    op.drop_index(index_name, table_name=table_name)
    op.create_index(index_name, table_name, columns, unique=False)


def _replace_plain_index_with_unique_index(index_name: str, table_name: str, columns: list[str]) -> None:
    op.drop_index(index_name, table_name=table_name)
    op.create_index(index_name, table_name, columns, unique=True)


def upgrade() -> None:
    _replace_unique_index_with_plain_index("ix_academic_years_label", "academic_years", ["label"])
    _replace_unique_index_with_plain_index("ix_departments_code", "departments", ["code"])
    _replace_unique_index_with_plain_index("ix_departments_name", "departments", ["name"])
    _replace_unique_index_with_plain_index("ix_rooms_room_number", "rooms", ["room_number"])
    _replace_unique_index_with_plain_index("ix_faculty_employee_id", "faculty", ["employee_id"])
    op.drop_constraint("uq_subject_code", "subjects", type_="unique")
    op.drop_constraint("uq_division_department_semester_name", "divisions", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_division_department_semester_name",
        "divisions",
        ["department_id", "semester_id", "name"],
    )
    op.create_unique_constraint("uq_subject_code", "subjects", ["code"])
    _replace_plain_index_with_unique_index("ix_faculty_employee_id", "faculty", ["employee_id"])
    _replace_plain_index_with_unique_index("ix_rooms_room_number", "rooms", ["room_number"])
    _replace_plain_index_with_unique_index("ix_departments_name", "departments", ["name"])
    _replace_plain_index_with_unique_index("ix_departments_code", "departments", ["code"])
    _replace_plain_index_with_unique_index("ix_academic_years_label", "academic_years", ["label"])
