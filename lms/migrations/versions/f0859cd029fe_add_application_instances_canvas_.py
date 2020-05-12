"""
Add application_instances.settings column.

Revision ID: f0859cd029fe
Revises: 37710e6bcb66
Create Date: 2020-05-06 15:48:13.964730

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

revision = "f0859cd029fe"
down_revision = "37710e6bcb66"


def upgrade():
    op.add_column(
        "application_instances", sa.Column("settings", MutableDict.as_mutable(JSONB)),
    )


def downgrade():
    op.drop_column("application_instances", "settings")
