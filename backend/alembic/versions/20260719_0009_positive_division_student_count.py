"""enforce positive division student counts

Revision ID: 20260719_0009
Revises: 20260719_0008
Create Date: 2026-07-19 00:09:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0009"
down_revision: str | None = "20260719_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM divisions WHERE student_count < 1) THEN
                RAISE EXCEPTION
                    'Cannot enforce positive division student counts: rows with fewer than 1 student exist';
            END IF;
        END $$;
        """
    )
    op.create_check_constraint(
        "ck_divisions_student_count_positive",
        "divisions",
        "student_count >= 1",
    )


def downgrade() -> None:
    op.drop_constraint("ck_divisions_student_count_positive", "divisions", type_="check")
