"""
Backfill "events" from lti_launches rows (2020).

Revision ID: 396f46318023
Revises: 42b39684836f
Create Date: 2022-08-17 15:16:52.785486

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "396f46318023"
down_revision = "42b39684836f"

BATCH_START_DATE = "2000-08-17T13:00:08.241"
BATCH_END_DATE = "2020-08-17T13:00:08.241"
"""
We'll do this in batches each bach between these two dates
"""

CUT_OFF_DATE = "2022-08-17T13:00:08.241"
"""
Date when we started inserting launches directly on events.
Rows in lti_launches would already have corresponding event after this date.

While doing this in batches this will the END_DATE of the last batch.
"""


def get_configured_launch_type_pk(conn):
    return conn.execute(
        "SELECT id from event_type WHERE type = 'configured_launch'"
    ).fetchone()[0]


def migrate_lti_launches(conn, start, end):
    launch_event_type_id = get_configured_launch_type_pk(conn)

    result = conn.execute(
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
                MAX(grouping.id)
        FROM lti_launches
        LEFT OUTER JOIN application_instances
            ON lti_launches.lti_key = application_instances.consumer_key
        LEFT OUTER JOIN grouping
            ON context_id = grouping.lms_id
                AND grouping.application_instance_id = application_instances.id
                AND grouping.type = 'course'
       -- Only backfill rows created before we also start tracking them directly on this table
        WHERE lti_launches.created >= '{start}' AND lti_launches.created < '{end}'
        -- We need to group by to pick one (MAX grouping.id) above of the possible
        -- multiple courses on the grouping table
        GROUP BY lti_launches.id, lti_launches.created, application_instances.id
        -- Ordering will keep new rows physically sorted on disk which should later help while querying
        ORDER BY lti_launches.created ASC
    """
    )
    print("\tInserted lti_launches rows into events:", result.rowcount)


def downgrade_lti_launches(conn, start, end):
    launch_event_type_id = get_configured_launch_type_pk(conn)

    result = conn.execute(
        f"""
        DELETE FROM event
        WHERE type_id = {launch_event_type_id}
            -- All events inserted by the forward version of this migration
            -- will have empty assignments.
            AND assignment_id is null
            AND timestamp >= '{start}' AND timestamp < '{end}'
    """
    )
    print("\tDeleted events rows:", result.rowcount)


def upgrade():
    conn = op.get_bind()

    migrate_lti_launches(conn, BATCH_START_DATE, BATCH_END_DATE)


def downgrade():
    conn = op.get_bind()

    downgrade_lti_launches(conn, BATCH_START_DATE, BATCH_END_DATE)
