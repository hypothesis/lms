"""Backfill LMSUserAssignmentMembership."""

import sqlalchemy as sa
from alembic import op

revision = "a9e5a33e96b7"
down_revision = "712c4c9a4e2e"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            SELECT
                assignment_membership.created,
                assignment_membership.updated,
                assignment_membership.assignment_id,
                lms_user.id as lms_user_id,
                lti_role_id
            FROM assignment_membership
            JOIN "user" on assignment_membership.user_id = "user".id
            JOIN "lms_user" on "user".h_userid = "lms_user".h_userid
        )
        INSERT INTO lms_user_assignment_membership (
             created,
             updated,
             assignment_id,
             lms_user_id,
             lti_role_id
        )
        SELECT
           created,
           updated,
           assignment_id,
           lms_user_id,
           lti_role_id
        FROM backfill
        -- We are already inserting rows in the table on the python code, leave those alone
        ON CONFLICT ON CONSTRAINT uq__lms_user_assignment_membership__assignment_id DO NOTHING
    """
        )
    )

    pass


def downgrade() -> None:
    pass
