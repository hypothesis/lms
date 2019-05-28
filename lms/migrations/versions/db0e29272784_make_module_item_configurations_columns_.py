"""
Make module_item_configurations columns not nullable.

Revision ID: db0e29272784
Revises: 4ab4d06f7e3f
Create Date: 2019-05-28 14:30:39.127153

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "db0e29272784"
down_revision = "4ab4d06f7e3f"


def upgrade():
    op.alter_column("module_item_configurations", "resource_link_id", nullable=False)
    op.alter_column(
        "module_item_configurations", "tool_consumer_instance_guid", nullable=False
    )
    op.alter_column("module_item_configurations", "document_url", nullable=False)


def downgrade():
    op.alter_column("module_item_configurations", "resource_link_id", nullable=True)
    op.alter_column(
        "module_item_configurations", "tool_consumer_instance_guid", nullable=True
    )
    op.alter_column("module_item_configurations", "document_url", nullable=True)
