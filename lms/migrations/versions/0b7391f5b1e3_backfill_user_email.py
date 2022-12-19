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

    # Flatten group_info.info.instructors
    conn.execute(
        """CREATE TEMPORARY VIEW group_info_instructors AS (
            SELECT
                group_info.application_instance_id,
                instructors.email,
                instructors.display_name,
                instructors.provider_unique_id,
                -- Rank emails by latest group_info.id
                row_number() over (partition by (instructors.provider_unique_id,  group_info.application_instance_id) order by group_info.id desc) as rank
            FROM
                group_info,
                jsonb_to_recordset(group_info.info->'instructors') as instructors(email text, username text, display_name text,provider_unique_id text )
        );"""
    )

    # Migrate emails
    result_emails = conn.execute(
        """
        UPDATE "user"
            SET email=group_info_emails.email
            FROM (
                SELECT "user".id, group_info_instructors.email
                FROM group_info_instructors
                LEFT OUTER JOIN "user" ON group_info_instructors.application_instance_id = "user".application_instance_id AND provider_unique_id = user_id
                WHERE
                    -- Only take the latest info from group_info for duplicates
                    rank = 1
                    -- Only take instructors that have an email in group_info
                    AND group_info_instructors.email IS NOT NULL AND group_info_instructors.email <> ''
                    --  And that we can match to a user in "user"
                    AND "user".id IS NOT NULL
                    -- Don't override any email we already had
                    AND "user".display_name IS NULL
            ) as group_info_emails
        WHERE "user".id = group_info_emails.id
    """
    )

    #  Migrate display_name
    result_names = conn.execute(
        """
        UPDATE "user"
            SET display_name=group_info_names.display_name
            FROM (
                SELECT "user".id, group_info_instructors.display_name
                FROM group_info_instructors
                LEFT OUTER JOIN "user" ON group_info_instructors.application_instance_id = "user".application_instance_id AND provider_unique_id = user_id
                WHERE
                    -- Only take the latest info from group_info for duplicates
                    rank = 1
                    -- Only take instructors that have a name in group_info
                    AND group_info_instructors.display_name IS NOT NULL AND group_info_instructors.display_name <> ''
                    --  And that we can match to a user in "user"
                    AND "user".id IS NOT NULL
                    -- Don't override any names we already had
                    AND "user".display_name IS NULL
            ) as group_info_names
        WHERE "user".id = group_info_names.id
    """
    )
    print("\tUpdated user rows with email from group_info:", result_emails.rowcount)
    print("\tUpdated user rows with names from group_info:", result_names.rowcount)


def downgrade():
    pass
