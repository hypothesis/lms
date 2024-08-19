"""LMSCourse backfill."""

import sqlalchemy as sa
from alembic import op

revision = "f61cb94edfc8"
down_revision = "9f31d4427a34"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            select distinct on (authority_provided_id)
                "grouping".created, "grouping".updated,
                tool_consumer_instance_guid, authority_provided_id, lms_name, lms_id
            from "grouping"
            join application_instances on application_instances.id = "grouping".application_instance_id
            where grouping.type ='course'
            order by authority_provided_id, "grouping".created desc
        )
        INSERT INTO lms_course (
             created,
             updated,
             tool_consumer_instance_guid,
             authority_provided_id,
             lti_id,
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
        ON CONFLICT (tool_consumer_instance_guid, lti_id) DO NOTHING
    """
        )
    )


def downgrade() -> None:
    pass
