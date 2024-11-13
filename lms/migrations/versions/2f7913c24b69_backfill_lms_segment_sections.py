"""Backfill lms_segment (sections)."""

import sqlalchemy as sa
from alembic import op

revision = "2f7913c24b69"
down_revision = "2ff20de04a9d"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        WITH backfill as (
            -- Deduplicate "grouping" sections on authority_provided_id
            SELECT DISTINCT ON (grouping.authority_provided_id)
                "grouping".created,
                "grouping".updated,
                grouping.authority_provided_id,
                grouping.lms_name,
                grouping.lms_id,
                "lms_course".id as lms_course_id
            FROM "grouping"
            -- Join grouping on itself to get the parent (course) data
            JOIN "grouping" parent on parent.id = grouping.parent_id
            -- Get the right LMSCourse row based on the parent
            JOIN lms_course on lms_course.h_authority_provided_id = parent.authority_provided_id
            -- Pick only sections
            WHERE grouping.type ='canvas_section'
            -- Pick the most recent version we've seen
            ORDER BY grouping.authority_provided_id, "grouping".updated desc
        )
        INSERT INTO lms_segment (
             created,
             updated,
             type,
             h_authority_provided_id,
             lms_id,
             name,
             lms_course_id
        )
        SELECT
           created,
           updated,
           'canvas_section',
           authority_provided_id,
           lms_id,
           lms_name,
           lms_course_id
        FROM backfill
        -- We are already inserting rows in lms_segment in the python code, leave those alone
        ON CONFLICT (h_authority_provided_id) DO NOTHING
    """)
    )


def downgrade() -> None:
    pass
