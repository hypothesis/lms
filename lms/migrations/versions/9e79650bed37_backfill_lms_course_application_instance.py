"""LMSCourseApplicationInstance backfill."""

import sqlalchemy as sa
from alembic import op

revision = "9e79650bed37"
down_revision = "e13fb37c96e5"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            SELECT
                "grouping".created,
                "grouping".updated,
                lms_course.id lms_course_id,
                "grouping".application_instance_id
            FROM "grouping"
            JOIN lms_course on lms_course.h_authority_provided_id = "grouping".authority_provided_id
        )
        INSERT INTO lms_course_application_instance (
             created,
             updated,
             lms_course_id,
             application_instance_id
        )
        SELECT
           created,
           updated,
           lms_course_id,
           application_instance_id
        FROM backfill
        ON CONFLICT (lms_course_id, application_instance_id) DO NOTHING
    """
        )
    )


def downgrade() -> None:
    pass
