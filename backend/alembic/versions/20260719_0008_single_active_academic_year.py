"""enforce a single active academic year

Revision ID: 20260719_0008
Revises: 20260719_0007
Create Date: 2026-07-19 00:08:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0008"
down_revision: str | None = "20260719_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF (SELECT count(*) FROM academic_years WHERE is_active IS TRUE) > 1 THEN
                RAISE EXCEPTION 'Cannot enforce active academic year uniqueness: multiple active rows exist';
            END IF;
        END $$;
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_academic_years_single_active "
        "ON academic_years ((is_active)) WHERE is_active IS TRUE"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_academic_years_single_active")
