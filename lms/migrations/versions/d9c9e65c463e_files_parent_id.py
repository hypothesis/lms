"""
Adds File.parent_lms_id.

Revision ID: d9c9e65c463e
Revises: da66efab9e5f
Create Date: 2021-08-09 16:39:49.615988

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9c9e65c463e"
down_revision = "da66efab9e5f"


def upgrade():
    op.add_column("file", sa.Column("parent_lms_id", sa.UnicodeText(), nullable=True))


def downgrade():
    op.drop_column("file", "parent_lms_id")
