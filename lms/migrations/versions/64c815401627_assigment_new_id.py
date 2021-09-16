"""
assigment_new_id

Revision ID: 64c815401627
Revises: d9c9e65c463e
Create Date: 2021-09-15 14:03:31.662572

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "64c815401627"
down_revision = "d9c9e65c463e"


def upgrade():
    op.add_column(
        "module_item_configurations",
        sa.Column("ext_lti_assignment_id", sa.Unicode(length=36), nullable=True),
    )
    op.alter_column(
        "module_item_configurations",
        "resource_link_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_unique_constraint(
        op.f("uq__module_item_configurations__ext_lti_assignment_id"),
        "module_item_configurations",
        ["ext_lti_assignment_id"],
    )
    op.create_check_constraint(
        "nullable_resource_link_id_ext_lti_assignment_id",
        table_name="module_item_configurations",
        condition="NOT(resource_link_id IS NULL AND ext_lti_assignment_id IS NULL)",
    )
    # TODO REMOVE on downgrade


def downgrade():
    op.drop_constraint(
        op.f("uq__module_item_configurations__ext_lti_assignment_id"),
        "module_item_configurations",
        type_="unique",
    )
    op.alter_column(
        "module_item_configurations",
        "resource_link_id",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.drop_column("module_item_configurations", "ext_lti_assignment_id")
