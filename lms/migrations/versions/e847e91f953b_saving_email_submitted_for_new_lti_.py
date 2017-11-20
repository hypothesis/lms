"""
Saving email submitted for new lti application.

Revision ID: e847e91f953b
Revises: a6a78f338d4a
Create Date: 2017-11-13 16:39:17.227758

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e847e91f953b'
down_revision = 'a6a78f338d4a'


def upgrade():
    op.add_column(
        'application_instances',
        sa.Column('requesters_email', sa.String),
        schema=None
    )


def downgrade():
    op.drop_column('application_instances', 'requesters_email')
