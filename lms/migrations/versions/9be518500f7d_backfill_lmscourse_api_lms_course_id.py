"""Backfill LMSCourse.api_lms_course_id."""

import sqlalchemy as sa
from alembic import op

revision = "9be518500f7d"
down_revision = "cf20e70211f9"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            -- Deduplicate "grouping" courses on authority_provided_id
            SELECT DISTINCT ON (authority_provided_id)
                authority_provided_id,
                extra->'canvas'->>'custom_canvas_course_id' as api_id
            FROM "grouping"
            -- Pick only courses, not sections or groups
            WHERE grouping.type ='course'
            -- Pick only courses with an API ID
            AND extra->'canvas'->>'custom_canvas_course_id' IS NOT NULL
            -- Pick the most recent "grouping" there are duplicates
            ORDER BY authority_provided_id, "grouping".updated desc
        )
        UPDATE lms_course
        SET
            lms_api_course_id = backfill.api_id
        FROM backfill
        WHERE
        lms_course.h_authority_provided_id = backfill.authority_provided_id
        -- We are already inserting rows in lms_course in the python code, leave those alone
        AND lms_course.lms_api_course_id IS NULL
    """
        )
    )


def downgrade() -> None:
    pass
