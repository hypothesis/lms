"""Backfill LMSUser

Revision ID: aef6a6460d0d
Revises: d1147f06adfc
"""
from alembic import op
import sqlalchemy as sa


revision = "aef6a6460d0d"
down_revision = "d1147f06adfc"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            select 
                distinct on (h_userid) 
                "user".created, "user".updated,
                tool_consumer_instance_guid, h_userid, user_id,email, 
                coalesce(
                  display_name,
                  (select display_name from "user" as user_2 where user_2.h_userid = "user".h_userid and display_name is not null limit 1)
                ) as display_name
            from "user"
            join application_instances on application_instances.id = "user".application_instance_id
            where tool_consumer_instance_guid is not null
            order by h_userid, "user".created desc
       )
        INSERT INTO lms_user (
             created,
             updated,
             tool_consumer_instance_guid,
             h_userid,
             lti_id,
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
        ON CONFLICT (tool_consumer_instance_guid, lti_id) DO NOTHING
    """
        )
    )


def downgrade() -> None:
    pass
