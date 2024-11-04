"""Backfill LMSGroupSet."""

import sqlalchemy as sa
from alembic import op

revision = "ba295703738b"
down_revision = "4b813a44a6c9"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            WITH backfill as (
                SELECT lms_course.id lms_course_id, course_group_sets.id group_set_id, course_group_sets.name group_set_name
                FROM grouping
                JOIN lms_course ON grouping.authority_provided_id = lms_course.h_authority_provided_id
                CROSS JOIN LATERAL jsonb_to_recordset(grouping.extra->'group_sets') as course_group_sets(id Text, name Text)
            )
            INSERT INTO lms_group_set (
                lms_course_id,
                lms_id,
                name
            )
            SELECT
                lms_course_id,
                group_set_id,
                group_set_name
            FROM backfill
            -- We are already inserting rows in the python code, leave those alone
            ON CONFLICT (lms_course_id, lms_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    pass
