"""
Delete no-longer-used DB tables.

Revision ID: 2fdc9b46320a
Revises: db0e29272784
Create Date: 2019-07-16 17:31:19.712970

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "2fdc9b46320a"
down_revision = "db0e29272784"


def upgrade():
    op.drop_table("oauth_state")
    op.drop_table("tokens")
    op.drop_table("users")


def downgrade():
    pass
