"""
Add oauth credentials to ApplicationInstance

Revision ID: 51889ae54178
Revises: 3802f4d2ec5c
Create Date: 2017-12-20 09:41:51.402587

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51889ae54178'
down_revision = '3802f4d2ec5c'


def upgrade():
    op.add_column(
        'application_instances',
        sa.Column('developer_key', sa.String)
    )

    op.add_column(
        'application_instances',
        sa.Column('developer_secret', sa.String)
    )




def downgrade():
    op.drop_column('application_instances', 'developer_key')
    op.drop_column('application_instances', 'developer_secret')
