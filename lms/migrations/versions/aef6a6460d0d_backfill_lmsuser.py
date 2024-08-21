"""Backfill LMSUser."""

import sqlalchemy as sa
from alembic import op

revision = "aef6a6460d0d"
down_revision = "1b80d29976d6"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            SELECT
                -- Deduplicate "user" on h_userid
                distinct on (h_userid)
                "user".created,
                "user".updated,
                tool_consumer_instance_guid,
                h_userid,
                user_id,
                email,
                -- Query display_name in case the most recently updated "user" is not the  one that has display_name
                coalesce(
                  display_name,
                  (select display_name from "user" as user_2 where user_2.h_userid = "user".h_userid and display_name is not null limit 1)
                ) as display_name
            FROM "user"
            -- join on application_instances to get the GUID
            JOIN application_instances on application_instances.id = "user".application_instance_id
            -- Pick the most recent "user" info when there are duplicates
            order by h_userid, "user".updated desc
        )
        INSERT INTO lms_user (
             created,
             updated,
             tool_consumer_instance_guid,
             h_userid,
             lti_user_id,
             email,
             display_name
        )
        SELECT
           created,
           updated,
           tool_consumer_instance_guid,
           h_userid,
           user_id,
           email,
           display_name
        FROM backfill
        -- We are already inserting rows in lms_user in the python code, leave those alone
        ON CONFLICT (h_userid) DO NOTHING
    """
        )
    )


def downgrade() -> None:
    pass
