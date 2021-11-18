"""
Enable MS OneDrive on instances that have previously been disabled.

Revision ID: 1693f6ade03d
Revises: 2fd66b9ab1a1
Create Date: 2021-11-18 10:47:24.773542

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1693f6ade03d"
down_revision = "2fd66b9ab1a1"


def upgrade():
    conn = op.get_bind()

    conn.execute(
        """UPDATE application_instances SET settings = settings || jsonb '{"microsoft_onedrive":{"files_enabled": true}}'
            WHERE settings -> 'microsoft_onedrive' -> 'files_enabled' = 'false';"""
    )


def downgrade():
    pass
