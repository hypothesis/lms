"""
Backfill user.email from group_info.

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

    result = conn.execute(
        """
        UPDATE "user"
        SET email=group_info_instructors.email
        FROM (
            WITH instructor_emails AS (
                SELECT
                    group_info.application_instance_id,
                    instructors.email,
                    instructors.provider_unique_id,
                    -- Rank emails by latest group_info.id
                    row_number() over (partition by (instructors.provider_unique_id,  group_info.application_instance_id) order by group_info.id desc) as rank
                FROM
                    group_info,
                    -- Flatten group_info.info.instructors
                    jsonb_to_recordset(group_info.info->'instructors') as instructors(email text, username text, display_name text,provider_unique_id text )
                -- Only take instructors that have an email in group_info
                WHERE instructors.email IS NOT NULL AND instructors.email <> ''
                
            )
            SELECT "user".id, instructor_emails.email
            FROM instructor_emails
            LEFT OUTER JOIN "user" ON instructor_emails.application_instance_id = "user".application_instance_id AND provider_unique_id = user_id
            WHERE
                -- Only take the lastest info from group_info for duplicates
                rank = 1
                --  And that we can match to a user in "user"
                AND "user".id IS NOT NULL

        ) as group_info_instructors
        WHERE "user".id = group_info_instructors.id
        -- Don't override any email we already had
        AND "user".email  IS NULL
    """
    )
    print("\tUpdated user rows with email from group_info:", result.rowcount)


def downgrade():
    pass
