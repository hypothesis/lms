"""
add_ext_lti_assignment_id

Revision ID: a58605fdd398
Revises: d9c9e65c463e
Create Date: 2021-09-17 07:59:11.487484

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a58605fdd398"
down_revision = "d9c9e65c463e"


def upgrade():
    op.add_column(
        "module_item_configurations",
        sa.Column("ext_lti_assignment_id", sa.UnicodeText(), nullable=True),
    )
    op.alter_column(
        "module_item_configurations",
        "resource_link_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_unique_constraint(
        op.f("uq__module_item_configurations__tool_consumer_instance_guid"),
        "module_item_configurations",
        ["tool_consumer_instance_guid", "ext_lti_assignment_id"],
    )

    op.create_check_constraint(
        "nullable_resource_link_id_ext_lti_assignment_id",
        table_name="module_item_configurations",
        condition="NOT(resource_link_id IS NULL AND ext_lti_assignment_id IS NULL)",
    )


def downgrade():
    op.drop_constraint(
        op.f("uq__module_item_configurations__tool_consumer_instance_guid"),
        "module_item_configurations",
        type_="unique",
    )
    op.alter_column(
        "module_item_configurations",
        "resource_link_id",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.drop_constraint(
        "nullable_resource_link_id_ext_lti_assignment_id",
        table_name="module_item_configurations",
        type_="check",
    )
    op.drop_column("module_item_configurations", "ext_lti_assignment_id")
