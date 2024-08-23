"""LMSCourse.copied_from_id backfill."""

import sqlalchemy as sa
from alembic import op

revision = "16ad8b08e0dd"
down_revision = "9e79650bed37"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            SELECT
                lms_course.id lms_course_id,
                copied_from_lms_course.id copied_from_id
            FROM "grouping"
            LEFT OUTER JOIN grouping copied_grouping on grouping.copied_from_id = copied_grouping.id
            JOIN lms_course on lms_course.authority_provided_id = "grouping".authority_provided_id
            LEFT OUTER JOIN lms_course copied_from_lms_course on copied_from_lms_course.authority_provided_id = "copied_grouping".authority_provided_id
            WHERE grouping.copied_from_id is not null
        )
        UPDATE lms_course
            set copied_from_id = backfill.copied_from_id
        FROM backfill
        WHERE lms_course.id = backfill.lms_course_id
        AND lms_course.copied_from_id is null
    """
        )
    )

    pass


def downgrade() -> None:
    pass
