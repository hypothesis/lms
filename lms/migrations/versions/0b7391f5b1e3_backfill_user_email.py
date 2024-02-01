"""
Backfill email and name from group_info.

Revision ID: 0b7391f5b1e3
Revises: e32d2cf33591
Create Date: 2022-12-19 10:42:00.577163

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0b7391f5b1e3"
down_revision = "e32d2cf33591"


def upgrade():
    conn = op.get_bind()

    conn.execute(
        """
        WITH user_details AS (
            SELECT
                "user".id,
                -- Pick the last non-empty value by group info id
                (
                    ARRAY_AGG(instructors.email ORDER BY group_info.id DESC)
                    FILTER (WHERE instructors.email IS NOT NULL AND instructors.email <> '')
                )[1] AS email,
                (
                    ARRAY_AGG(instructors.display_name ORDER BY group_info.id DESC)
                    FILTER (WHERE instructors.display_name IS NOT NULL AND instructors.display_name <> '')
                )[1] AS display_name
            FROM
                group_info
            CROSS JOIN LATERAL
                jsonb_to_recordset(group_info.info->'instructors') AS instructors(email text, display_name text, provider_unique_id text)
            JOIN "user" ON
                "user".application_instance_id = group_info.application_instance_id
                AND "user".user_id = instructors.provider_unique_id
            GROUP BY "user".id
        )
    UPDATE "user"
    SET
        -- Only overwrite nulls
        email=COALESCE("user".email, user_details.email),
        display_name=COALESCE("user".display_name, user_details.display_name)
    FROM user_details
    WHERE "user".id = user_details.id
    """
    )


def downgrade():
    pass
