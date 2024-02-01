"""
Enable email digest (batch 04).

Revision ID: 3a786e91f59c
Revises: 9207d2192903
Create Date: 2023-05-25 09:46:18.988105

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

revision = "3a786e91f59c"
down_revision = "9207d2192903"


def upgrade():
    conn = op.get_bind()
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
            SELECT distinct application_instances.id
            FROM application_instances
            WHERE  COALESCE(settings->'hypothesis'->>'instructor_email_digests_enabled', 'false') = 'false'
        ) AS candidates
        WHERE
            application_instances.id = candidates.id"""
        )
    )
    print("\tEnabled email digest in new AIs", result.rowcount)


def downgrade():
    """No downgrade section as we might manually change some values after running `upgrade`."""
    pass
