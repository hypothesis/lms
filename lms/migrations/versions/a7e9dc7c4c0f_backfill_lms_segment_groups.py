"""Backfill lms_segment (groups)."""

import sqlalchemy as sa
from alembic import op

revision = "a7e9dc7c4c0f"
down_revision = "2f7913c24b69"


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
                "lms_course".id as lms_course_id,
                grouping.type,
                lms_group_set.id as lms_group_set_id
            FROM "grouping"
            -- Join grouping on itself to get the parent (course) data
            JOIN "grouping" parent on parent.id = grouping.parent_id
            -- Get the right LMSCourse row based on the parent
            JOIN lms_course on lms_course.h_authority_provided_id = parent.authority_provided_id
            LEFT OUTER JOIN lms_group_set ON lms_group_set.lms_course_id = lms_course.id and lms_group_set.lms_id = grouping.extra->>'group_set_id'::text
            -- Pick only groups
            WHERE grouping.type <> 'canvas_section' and grouping.parent_id is not null
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
             lms_course_id,
             lms_group_set_id
        )
        SELECT
           created,
           updated,
           type,
           authority_provided_id,
           lms_id,
           lms_name,
           lms_course_id,
           lms_group_set_id
        FROM backfill
        -- We are already inserting rows in lms_segment in the python code, leave those alone
        ON CONFLICT (h_authority_provided_id) DO NOTHING
    """)
    )


def downgrade() -> None:
    pass
