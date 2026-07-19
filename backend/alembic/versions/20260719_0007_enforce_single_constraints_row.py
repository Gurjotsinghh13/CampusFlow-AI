"""enforce singleton scheduling constraints row

Revision ID: 20260719_0007
Revises: 20260719_0006
Create Date: 2026-07-19 00:07:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0007"
down_revision: str | None = "20260719_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF (SELECT count(*) FROM constraints) > 1 THEN
                RAISE EXCEPTION 'Cannot enforce singleton constraints row: multiple rows exist';
            END IF;
        END $$;
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_constraints_singleton ON constraints ((true))")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_constraints_singleton")
