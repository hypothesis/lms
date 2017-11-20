"""
Add application url and datestamp

Revision ID: 58f2693de313
Revises: a6a78f338d4a
Create Date: 2017-11-20 16:40:26.060862

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '58f2693de313'
down_revision = 'a6a78f338d4a'


def upgrade():
    op.add_column(
        'application_instances',
        sa.Column('created', sa.TIMESTAMP, default=datetime.utcnow)
    )

    op.add_column(
        'application_instances',
        sa.Column('requesters_email', sa.String),
        schema=None
    )


def downgrade():
    op.drop_column('application_instances', 'requesters_email')
    op.drop_column('application_instances', 'created')
