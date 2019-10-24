"""
Add application_instance model.

Revision ID: d9e4bc3797b3
Revises: f013a6b67f91
Create Date: 2017-10-31 09:49:40.491059

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9e4bc3797b3"
down_revision = "f013a6b67f91"


def upgrade():
    op.create_table(
        "application_instances",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("consumer_key", sa.String),
        sa.Column("shared_secret", sa.String),
        sa.Column("lms_url", sa.String(2048)),
    )


def downgrade():
    pass
