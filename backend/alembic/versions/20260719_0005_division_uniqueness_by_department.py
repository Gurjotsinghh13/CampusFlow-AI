"""scope division uniqueness to department and semester

Revision ID: 20260719_0005
Revises: 20260719_0004
Create Date: 2026-07-19 00:05:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0005"
down_revision: str | None = "20260719_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT department_id, semester_id, lower(btrim(name))
                FROM divisions
                GROUP BY department_id, semester_id, lower(btrim(name))
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Duplicate division names exist per department and semester';
            END IF;
        END $$;
        """
    )
    op.execute("DROP INDEX IF EXISTS uq_divisions_semester_name_lower")
    op.drop_constraint("uq_division_semester_name", "divisions", type_="unique")
    op.create_unique_constraint(
        "uq_division_department_semester_name",
        "divisions",
        ["department_id", "semester_id", "name"],
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_divisions_department_semester_name_lower "
        "ON divisions (department_id, semester_id, lower(btrim(name)))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_divisions_department_semester_name_lower")
    op.drop_constraint("uq_division_department_semester_name", "divisions", type_="unique")
    op.create_unique_constraint("uq_division_semester_name", "divisions", ["semester_id", "name"])
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_divisions_semester_name_lower "
        "ON divisions (semester_id, lower(btrim(name)))"
    )
