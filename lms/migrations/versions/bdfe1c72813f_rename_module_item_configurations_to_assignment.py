"""
Rename module_item_configurations to assignment.

Revision ID: bdfe1c72813f
Revises: 911d1f7da759
Create Date: 2022-05-26 14:45:34.578511

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bdfe1c72813f"
down_revision = "911d1f7da759"


ITEMS = (
    ("INDEX", "pk__module_item_configurations", "pk__assignment"),
    (
        "INDEX",
        "uq__module_item_configurations__resource_link_id",
        "uq__assignment__resource_link_id",
    ),
    (
        "INDEX",
        "uq__module_item_configurations__tool_consumer_instance_guid",
        "uq__assignment__tool_consumer_instance_guid",
    ),
    ("SEQUENCE", "module_item_configurations_id_seq", "assignment_id_seq"),
)


def upgrade():
    # I don't think you can rename constraints, so we have to drop and recreate
    # them. When removing constraints we must use the full generated name
    op.drop_constraint(
        "ck__module_item_configurations__nullable_resource_link__081b",
        "module_item_configurations",
    )
    op.rename_table("module_item_configurations", "assignment")

    # Re-create the constraint after the table renaming to get the correct auto
    # generated name
    op.create_check_constraint(
        "nullable_resource_link_id_ext_lti_assignment_id",
        table_name="assignment",
        condition="NOT(resource_link_id IS NULL AND ext_lti_assignment_id IS NULL)",
    )

    for item_type, old_name, new_name in ITEMS:
        op.execute(f"ALTER {item_type} {old_name} RENAME TO {new_name}")

    op.execute("CREATE VIEW module_item_configurations AS (SELECT * FROM assignment)")


def downgrade():
    op.execute("DROP VIEW module_item_configurations")

    op.drop_constraint(
        "ck__assignment__nullable_resource_link_id_ext_lti_assignment_id", "assignment"
    )
    op.rename_table("assignment", "module_item_configurations")

    for item_type, old_name, new_name in ITEMS:
        op.execute(f"ALTER {item_type} {new_name} RENAME TO {old_name}")

    op.create_check_constraint(
        "nullable_resource_link_id_ext_lti_assignment_id",
        table_name="module_item_configurations",
        condition="NOT(resource_link_id IS NULL AND ext_lti_assignment_id IS NULL)",
    )
