"""add generated timetable academic year snapshot

Revision ID: 20260719_0003
Revises: 20260719_0002
Create Date: 2026-07-19 00:03:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260719_0003"
down_revision: str | None = "20260719_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("generated_timetables", sa.Column("academic_year_label", sa.String(length=20), nullable=True))
    op.execute(
        """
        UPDATE generated_timetables AS gt
        SET academic_year_label = ay.label
        FROM academic_years AS ay
        WHERE gt.academic_year_id = ay.id
        """
    )
    op.alter_column("generated_timetables", "academic_year_label", nullable=False)


def downgrade() -> None:
    op.drop_column("generated_timetables", "academic_year_label")
