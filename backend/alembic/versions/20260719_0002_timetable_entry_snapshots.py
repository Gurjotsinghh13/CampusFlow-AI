"""add timetable entry snapshots

Revision ID: 20260719_0002
Revises: 20260719_0001
Create Date: 2026-07-19 00:02:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260719_0002"
down_revision: str | None = "20260719_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("timetable_entries", sa.Column("division_name", sa.String(length=20), nullable=True))
    op.add_column("timetable_entries", sa.Column("subject_name", sa.String(length=150), nullable=True))
    op.add_column("timetable_entries", sa.Column("subject_code", sa.String(length=20), nullable=True))
    op.add_column("timetable_entries", sa.Column("faculty_name", sa.String(length=150), nullable=True))
    op.add_column("timetable_entries", sa.Column("room_number", sa.String(length=20), nullable=True))

    op.execute(
        """
        UPDATE timetable_entries AS te
        SET division_name = d.name
        FROM divisions AS d
        WHERE te.division_id = d.id
        """
    )
    op.execute(
        """
        UPDATE timetable_entries AS te
        SET subject_name = s.name,
            subject_code = s.code
        FROM subjects AS s
        WHERE te.subject_id = s.id
        """
    )
    op.execute(
        """
        UPDATE timetable_entries AS te
        SET faculty_name = f.full_name
        FROM faculty AS f
        WHERE te.faculty_id = f.id
        """
    )
    op.execute(
        """
        UPDATE timetable_entries AS te
        SET room_number = r.room_number
        FROM rooms AS r
        WHERE te.room_id = r.id
        """
    )

    op.alter_column("timetable_entries", "division_name", nullable=False)
    op.alter_column("timetable_entries", "subject_name", nullable=False)
    op.alter_column("timetable_entries", "subject_code", nullable=False)
    op.alter_column("timetable_entries", "faculty_name", nullable=False)
    op.alter_column("timetable_entries", "room_number", nullable=False)


def downgrade() -> None:
    op.drop_column("timetable_entries", "room_number")
    op.drop_column("timetable_entries", "faculty_name")
    op.drop_column("timetable_entries", "subject_code")
    op.drop_column("timetable_entries", "subject_name")
    op.drop_column("timetable_entries", "division_name")
