"""
Enable email digest (batch 01).

Revision ID: b11713314988
Revises: a58408aa13ab
Create Date: 2023-05-15 11:12:17.057567

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "b11713314988"
down_revision = "a58408aa13ab"


def enable_email_digest(conn, limit=500):
    result = conn.execute(
        text(
            """
        UPDATE application_instances
            SET settings = CASE
                WHEN settings = '{}' THEN '{"hypothesis": {"instructor_email_digests_enabled": true}}'
                WHEN settings->'hypothesis' IS NULL THEN jsonb_set(settings, '{hypothesis}', '{"instructor_email_digests_enabled": true}')
                ELSE jsonb_set(settings, '{hypothesis,instructor_email_digests_enabled}', 'true')
            END
        FROM (
            SELECT distinct application_instance_id, count("user".id)
            FROM assignment_membership
            JOIN "user" ON "user".id = assignment_membership.user_id
            JOIN lti_role ON lti_role.id = lti_role_id
            JOIN application_instances ON application_instance_id = application_instances.id
            WHERE
                -- Teachers
                type ='instructor' AND scope = 'course'
                -- AIs with some recent activity
                AND last_launched >= '2023-01-01'
                -- With the feature currently disabled
                AND COALESCE(settings->'hypothesis'->>'instructor_email_digests_enabled', 'false') = 'false'
            GROUP BY application_instance_id, "user".id
            -- Least used first
            ORDER BY COUNT("user".id) ASC, application_instance_id
            LIMIT :limit
        ) AS candidates
        WHERE
            application_instances.id = candidates.application_instance_id"""
        ),
        limit=limit,
    )
    print("\tEnabled email digest in new AIs", result.rowcount)


def upgrade():
    conn = op.get_bind()
    enable_email_digest(conn, 500)


def downgrade():
    """No downgrade section as we might manually change some values after running `upgrade`."""
    pass
