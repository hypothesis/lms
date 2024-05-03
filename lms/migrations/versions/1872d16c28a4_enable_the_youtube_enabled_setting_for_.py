"""Enable the youtube.enabled setting for all application instances.

Set the youtube.enabled setting to true for all application instances that
currently have it explicitly set to false in the DB.

Revision ID: 1872d16c28a4
Revises: 106d94be7705
"""

from alembic import op

revision = "1872d16c28a4"
down_revision = "106d94be7705"


def upgrade() -> None:
    op.get_bind().execute(
        """UPDATE application_instances
           SET settings = settings || jsonb '{"youtube":{"enabled": true}}'
           WHERE settings -> 'youtube' -> 'enabled' = 'false';"""
    )


def downgrade() -> None:
    pass
