"""LMSCourse backfill."""

import sqlalchemy as sa
from alembic import op

revision = "f61cb94edfc8"
down_revision = "aef6a6460d0d"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            -- Deduplicate "grouping" courses on authority_provided_id
            SELECT DISTINCT ON (authority_provided_id)
                "grouping".created,
                "grouping".updated,
                tool_consumer_instance_guid,
                authority_provided_id,
                lms_name,
                lms_id
            FROM "grouping"
            -- join on application_instances to get the GUID
            JOIN application_instances on application_instances.id = "grouping".application_instance_id
            -- Pick only courses, not sections or groups
            WHERE grouping.type ='course'
            -- Pick the most recent "grouping" there are duplicates
            ORDER BY authority_provided_id, "grouping".updated desc
        )
        INSERT INTO lms_course (
             created,
             updated,
             tool_consumer_instance_guid,
             h_authority_provided_id,
             lti_context_id,
             name
        )
        SELECT
           created,
           updated,
           tool_consumer_instance_guid,
           authority_provided_id,
           lms_id,
           lms_name
        FROM backfill
        -- We are already inserting rows in lms_course in the python code, leave those alone
        ON CONFLICT (h_authority_provided_id) DO NOTHING
    """
        )
    )


def downgrade() -> None:
    pass
