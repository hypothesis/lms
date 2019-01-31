"""
Remove the course_groups table.

Revision ID: 83f18f61c76a
Revises: b99c4d910801
Create Date: 2019-01-31 13:31:19.842973

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "83f18f61c76a"
down_revision = "b99c4d910801"


def upgrade():
    op.drop_table("course_groups")


def downgrade():
    pass
