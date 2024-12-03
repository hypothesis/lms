"""
Backfill grouping with courses based on rows from `course` and `group_info`.

Revision ID: 911d1f7da759
Revises: 2119e1c621de
Create Date: 2022-03-25 11:35:19.760847

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "911d1f7da759"
down_revision = "34f28d992b18"


def upgrade():
    conn = op.get_bind()

    conn.execute(
        """
        INSERT INTO grouping
            (
                created,
                updated,
                application_instance_id,
                authority_provided_id,
                parent_id,
                lms_id,
                lms_name,
                type,
                settings,
                extra
            )
        SELECT
                -- Using a hard-coded value in the past to identify the rows added by the migration
                '2022-03-25 00:00:00',
                '2022-03-25 00:00:00',
                application_instances.id,
                group_info.authority_provided_id,
                -- No parent
                NULL,
                group_info.context_id,
                group_info.context_title,
                'course',
                course.settings,
                CASE
                    WHEN group_info.custom_canvas_course_id is null
                    THEN  '{}'
                    ELSE jsonb_build_object(
                        'canvas', jsonb_build_object('custom_canvas_course_id', custom_canvas_course_id)
                    )
                END
        FROM course
        -- Make sure the group_info row is for the same course in the same application_instance
        JOIN group_info
            ON course.authority_provided_id = group_info.authority_provided_id
            AND group_info.consumer_key = course.consumer_key
        -- We'll get the application_instance_id from application_instances
        JOIN application_instances
            ON course.consumer_key = application_instances.consumer_key
        WHERE
            -- Ignore courses for application_instances for which we don't have a guid
            application_instances.tool_consumer_instance_guid IS NOT NULL
            -- Only bring courses for which the guid we have in application_instances matches the one in group_info
            AND application_instances.tool_consumer_instance_guid = group_info.tool_consumer_instance_guid
        -- Don't duplicate or update  courses we already have in grouping
        ON CONFLICT (application_instance_id, authority_provided_id) DO NOTHING
    """
    )


def downgrade():
    conn = op.get_bind()

    conn.execute(
        "DELETE FROM grouping WHERE created = '2022-03-25 00:00:00' AND type = 'course'"
    )
