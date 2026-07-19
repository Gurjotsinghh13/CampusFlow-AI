"""prevent master-data deletes from erasing timetable history

Revision ID: 20260719_0006
Revises: 20260719_0005
Create Date: 2026-07-19 00:06:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0006"
down_revision: str | None = "20260719_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("generated_timetables_academic_year_id_fkey", "generated_timetables", type_="foreignkey")
    op.create_foreign_key(
        "generated_timetables_academic_year_id_fkey",
        "generated_timetables",
        "academic_years",
        ["academic_year_id"],
        ["id"],
    )

    for column, target_table in (
        ("division_id", "divisions"),
        ("subject_id", "subjects"),
        ("faculty_id", "faculty"),
        ("room_id", "rooms"),
    ):
        constraint_name = f"timetable_entries_{column}_fkey"
        op.drop_constraint(constraint_name, "timetable_entries", type_="foreignkey")
        op.create_foreign_key(
            constraint_name,
            "timetable_entries",
            target_table,
            [column],
            ["id"],
        )


def downgrade() -> None:
    op.drop_constraint("generated_timetables_academic_year_id_fkey", "generated_timetables", type_="foreignkey")
    op.create_foreign_key(
        "generated_timetables_academic_year_id_fkey",
        "generated_timetables",
        "academic_years",
        ["academic_year_id"],
        ["id"],
        ondelete="CASCADE",
    )

    for column, target_table in (
        ("division_id", "divisions"),
        ("subject_id", "subjects"),
        ("faculty_id", "faculty"),
        ("room_id", "rooms"),
    ):
        constraint_name = f"timetable_entries_{column}_fkey"
        op.drop_constraint(constraint_name, "timetable_entries", type_="foreignkey")
        op.create_foreign_key(
            constraint_name,
            "timetable_entries",
            target_table,
            [column],
            ["id"],
            ondelete="CASCADE",
        )
