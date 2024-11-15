"""Backfill lms_course_membership."""

import sqlalchemy as sa
from alembic import op

revision = "50fb51c51314"
down_revision = "a7e9dc7c4c0f"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        WITH backfill as (
            select lms_course.id lms_course_id, lms_user.id as lms_user_id, lti_role_id, min(assignment_membership.created) created, max(assignment_membership.updated) updated
            from assignment_membership
            join assignment on assignment_id = assignment.id join grouping on grouping.id = course_id
            join lms_course on lms_course.h_authority_provided_id = grouping.authority_provided_id
            join "user" on "user".id = assignment_membership.user_id
            join  lms_user on lms_user.h_userid = "user".h_userid
            group by lms_course.id, lms_user.id, lti_role_id
        )
        INSERT INTO lms_course_membership (
            created,
            updated,
            lms_course_id,
            lms_user_id,
            lti_role_id
        )
        SELECT
           created,
           updated,
           lms_course_id,
           lms_user_id,
           lti_role_id
        FROM backfill
        -- We are already inserting rows in the membership table in the python code, leave those alone
        ON CONFLICT (lms_course_id, lms_user_id, lti_role_id) DO NOTHING
    """)
    )


def downgrade() -> None:
    pass
