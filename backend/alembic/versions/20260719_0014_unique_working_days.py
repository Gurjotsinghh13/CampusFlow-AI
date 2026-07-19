"""enforce unique working days

Revision ID: 20260719_0014
Revises: 20260719_0013
Create Date: 2026-07-19 00:14:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0014"
down_revision: str | None = "20260719_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

WORKING_DAYS_UNIQUE = (
    "COALESCE(cardinality(array_positions(working_days, 'MONDAY')), 0) <= 1 AND "
    "COALESCE(cardinality(array_positions(working_days, 'TUESDAY')), 0) <= 1 AND "
    "COALESCE(cardinality(array_positions(working_days, 'WEDNESDAY')), 0) <= 1 AND "
    "COALESCE(cardinality(array_positions(working_days, 'THURSDAY')), 0) <= 1 AND "
    "COALESCE(cardinality(array_positions(working_days, 'FRIDAY')), 0) <= 1 AND "
    "COALESCE(cardinality(array_positions(working_days, 'SATURDAY')), 0) <= 1 AND "
    "COALESCE(cardinality(array_positions(working_days, 'SUNDAY')), 0) <= 1"
)


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM constraints
                WHERE NOT ({WORKING_DAYS_UNIQUE})
            ) THEN
                RAISE EXCEPTION 'Cannot enforce unique scheduling working days: duplicate days exist';
            END IF;
            IF EXISTS (
                SELECT 1 FROM generated_timetables
                WHERE NOT ({WORKING_DAYS_UNIQUE})
            ) THEN
                RAISE EXCEPTION 'Cannot enforce unique generated timetable working days: duplicate days exist';
            END IF;
        END $$;
        """
    )
    op.create_check_constraint("ck_constraints_working_days_unique", "constraints", WORKING_DAYS_UNIQUE)
    op.create_check_constraint(
        "ck_generated_timetables_working_days_unique",
        "generated_timetables",
        WORKING_DAYS_UNIQUE,
    )


def downgrade() -> None:
    op.drop_constraint("ck_generated_timetables_working_days_unique", "generated_timetables", type_="check")
    op.drop_constraint("ck_constraints_working_days_unique", "constraints", type_="check")
