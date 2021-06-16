"""
Add assignment extras column.

Revision ID: bf67a1e68cea
Revises: 47d738f87eb5
Create Date: 2021-06-16 12:19:17.417022

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bf67a1e68cea"
down_revision = "47d738f87eb5"


def upgrade():
    op.add_column(
        "module_item_configurations",
        sa.Column(
            "extra",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("module_item_configurations", "extra")
