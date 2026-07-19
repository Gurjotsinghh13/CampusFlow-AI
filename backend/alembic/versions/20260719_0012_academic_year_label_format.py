"""enforce academic year label format

Revision ID: 20260719_0012
Revises: 20260719_0011
Create Date: 2026-07-19 00:12:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0012"
down_revision: str | None = "20260719_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM academic_years WHERE NOT (label ~ '^[0-9]{4}-[0-9]{4}$')) THEN
                RAISE EXCEPTION 'Cannot enforce academic year format: invalid labels exist';
            END IF;
        END $$;
        """
    )
    op.create_check_constraint(
        "ck_academic_years_label_format",
        "academic_years",
        "label ~ '^[0-9]{4}-[0-9]{4}$'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_academic_years_label_format", "academic_years", type_="check")
