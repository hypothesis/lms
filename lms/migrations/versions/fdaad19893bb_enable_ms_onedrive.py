"""
Enable MS OneDrive files in all installations created since Jan 1st, 2019.

Revision ID: fdaad19893bb
Revises: 2fd66b9ab1a1
Create Date: 2021-11-12 13:36:11.755526

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fdaad19893bb"
down_revision = "2fd66b9ab1a1"


def upgrade():
    conn = op.get_bind()

    conn.execute(
        """
        UPDATE application_instances
            SET settings = settings || jsonb '{"microsoft_onedrive":{"files_enabled": true}}'
        WHERE created >= '2019-01-01'::date
            AND developer_key is not null"""
    )


def downgrade():
    pass
