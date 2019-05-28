"""
Add unique constraint to module_item_configurations.

Revision ID: 4ab4d06f7e3f
Revises: f36f9a0aadf4
Create Date: 2019-05-28 14:08:38.790749

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "4ab4d06f7e3f"
down_revision = "f36f9a0aadf4"


def upgrade():
    op.create_unique_constraint(
        "uq__module_item_configurations__resource_link_id",
        "module_item_configurations",
        ["resource_link_id", "tool_consumer_instance_guid"],
    )


def downgrade():
    op.drop_constraint(
        "uq__module_item_configurations__resource_link_id", "module_item_configurations"
    )
