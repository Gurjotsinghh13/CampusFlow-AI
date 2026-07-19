"""enforce consecutive academic year labels

Revision ID: 20260719_0013
Revises: 20260719_0012
Create Date: 2026-07-19 00:13:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260719_0013"
down_revision: str | None = "20260719_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ACADEMIC_YEAR_LABEL_FORMAT = "'^[0-9]{4}-[0-9]{4}$'"
ACADEMIC_YEAR_LABEL_CONSECUTIVE = (
    f"CASE WHEN label ~ {ACADEMIC_YEAR_LABEL_FORMAT} "
    "THEN substring(label from 6 for 4)::integer = substring(label from 1 for 4)::integer + 1 "
    "ELSE false END"
)
GENERATED_LABEL_CONSECUTIVE = (
    f"CASE WHEN academic_year_label ~ {ACADEMIC_YEAR_LABEL_FORMAT} "
    "THEN substring(academic_year_label from 6 for 4)::integer = "
    "substring(academic_year_label from 1 for 4)::integer + 1 "
    "ELSE false END"
)


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM academic_years
                WHERE NOT (label ~ {ACADEMIC_YEAR_LABEL_FORMAT})
                   OR NOT ({ACADEMIC_YEAR_LABEL_CONSECUTIVE})
            ) THEN
                RAISE EXCEPTION 'Cannot enforce academic year sequence: invalid labels exist';
            END IF;
            IF EXISTS (
                SELECT 1 FROM generated_timetables
                WHERE NOT (academic_year_label ~ {ACADEMIC_YEAR_LABEL_FORMAT})
                   OR NOT ({GENERATED_LABEL_CONSECUTIVE})
            ) THEN
                RAISE EXCEPTION 'Cannot enforce generated timetable academic year sequence: invalid labels exist';
            END IF;
        END $$;
        """
    )
    op.create_check_constraint(
        "ck_academic_years_label_consecutive",
        "academic_years",
        ACADEMIC_YEAR_LABEL_CONSECUTIVE,
    )
    op.create_check_constraint(
        "ck_generated_timetables_academic_year_label_format",
        "generated_timetables",
        f"academic_year_label ~ {ACADEMIC_YEAR_LABEL_FORMAT}",
    )
    op.create_check_constraint(
        "ck_generated_timetables_academic_year_label_consecutive",
        "generated_timetables",
        GENERATED_LABEL_CONSECUTIVE,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_generated_timetables_academic_year_label_consecutive",
        "generated_timetables",
        type_="check",
    )
    op.drop_constraint(
        "ck_generated_timetables_academic_year_label_format",
        "generated_timetables",
        type_="check",
    )
    op.drop_constraint("ck_academic_years_label_consecutive", "academic_years", type_="check")
