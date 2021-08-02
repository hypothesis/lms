"""
Enable canvas groups in all installations craeted since Jan 1st, 2019.

Revision ID: da66efab9e5f
Revises: bf67a1e68cea
Create Date: 2021-08-02 08:18:29.729262

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "da66efab9e5f"
down_revision = "bf67a1e68cea"


def upgrade():
    conn = op.get_bind()

    conn.execute(
        "UPDATE application_instances SET settings = jsonb_set(settings, '{canvas,groups_enabled}', 'true') WHERE created >= '2019-01-01'::date and settings <> '{}' and developer_key is not null"
    )
    conn.execute(
        """UPDATE application_instances SET settings = '{"canvas": {"groups_enabled": true}}' WHERE created >= '2019-01-01'::date and settings = '{}' and developer_key is not null"""
    )


def downgrade():
    pass
