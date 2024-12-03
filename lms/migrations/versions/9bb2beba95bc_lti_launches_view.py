"""
Create backwards compatible `lti_launches` view.

Revision ID: 9bb2beba95bc
Revises: 396f46318023
Create Date: 2022-08-18 13:46:57.526511

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9bb2beba95bc"
down_revision = "396f46318023"


def upgrade():
    conn = op.get_bind()
    launch_event_type_id = conn.execute(
        "SELECT id from event_type WHERE type = 'configured_launch'"
    ).fetchone()[0]

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
    op.execute("DROP VIEW lti_launches")
    op.execute("ALTER TABLE old_lti_launches RENAME TO lti_launches")
