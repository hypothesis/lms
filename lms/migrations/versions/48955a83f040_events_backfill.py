"""
Backfills the events table using the data from  `lti_launches`.

Also renames the table and create a view with the same name to keep 
any reports based on it backward compatible.


Revision ID: 48955a83f040
Revises: 42b39684836f
Create Date: 2022-08-01 14:30:34.211522

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "48955a83f040"
down_revision = "42b39684836f"


def upgrade():
    conn = op.get_bind()

    launch_event_type_id = conn.execute(
        "SELECT id from event_type WHERE type = 'configured_launch'"
    ).fetchone()[0]

    conn.execute(
        f"""
        INSERT INTO event
            (
                timestamp,
                type_id,
                application_instance_id,
                course_id
            )
        SELECT
                lti_launches.created,
                {launch_event_type_id},
                application_instances.id,
                grouping.id
        FROM lti_launches
        JOIN application_instances
            ON lti_launches.lti_key = application_instances.consumer_key
        JOIN grouping
            ON context_id = grouping.lms_id and grouping.application_instance_id = application_instances.id and grouping.type = 'course'
    """
    )

    # Rename the existing table to leave the name free for the view.
    # We'll delete it after a while.
    op.execute("ALTER TABLE lti_launches RENAME TO old_lti_launches")

    # Create a view with the sane name as the old table, queries that used the old one
    # should work without any changes in the new events table.
    op.execute(
        f"""CREATE VIEW lti_launches AS (
            SELECT 
                event.id, 
                event.timestamp AS created,
                grouping.lms_id AS context_id,
                application_instances.consumer_key AS lti_key
            FROM event
            JOIN application_instances 
                ON event.application_instance_id = application_instances.id
            JOIN grouping 
                ON event.course_id = grouping.id
            WHERE event.type_id = {launch_event_type_id}
        )"""
    )


def downgrade():
    pass
