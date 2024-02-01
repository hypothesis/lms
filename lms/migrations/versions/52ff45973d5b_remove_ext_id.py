"""
Remove assignment.ext_lti_assignment_id.

Revision ID: 52ff45973d5b
Revises: bdfe1c72813f
Create Date: 2022-06-03 12:58:54.487617

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "52ff45973d5b"
down_revision = "bdfe1c72813f"


def upgrade():
    conn = op.get_bind()

    # Before we can make resource_link_id not nullable we must delete
    # some rows that have nulls there.
    # These rows belong to assignments configured but never launched in Canvas
    # during the brief period of time the code using ext_lti_assignment_id was live
    result = conn.execute(
        """
        DELETE FROM assignment WHERE
            ext_lti_assignment_id IS NOT NULL
            AND resource_link_id IS NULL"""
    )
    # We expect this to affect no more that 3 rows after checking the data in production.
    assert result.rowcount <= 3, "Trying to delete more rows that expected"

    # Make resource_link_id not nullable
    op.alter_column(
        "assignment", "resource_link_id", existing_type=sa.VARCHAR(), nullable=False
    )

    # Drop the constraints affecting ext_lti_assignment_id
    # The oddly named uq__assignment__tool_consumer_instance_guid
    # From \d assignment:
    #   "uq__assignment__tool_consumer_instance_guid" UNIQUE CONSTRAINT, btree (tool_consumer_instance_guid, ext_lti_assignment_id)
    op.drop_constraint(
        "uq__assignment__tool_consumer_instance_guid", "assignment", type_="unique"
    )
    op.drop_constraint(
        "nullable_resource_link_id_ext_lti_assignment_id",
        table_name="assignment",
        type_="check",
    )

    # Temporally drop the view based on assignments
    op.execute("DROP VIEW IF EXISTS module_item_configurations")
    # Drop the column
    op.drop_column("assignment", "ext_lti_assignment_id")
    # Regenerate `module_item_configurations" after the changes to the "source" table
    op.execute("CREATE VIEW module_item_configurations AS (SELECT * FROM assignment)")


def downgrade():
    op.add_column(
        "assignment",
        sa.Column(
            "ext_lti_assignment_id", sa.TEXT(), autoincrement=False, nullable=True
        ),
    )
    op.create_unique_constraint(
        "uq__assignment__tool_consumer_instance_guid",
        "assignment",
        ["tool_consumer_instance_guid", "ext_lti_assignment_id"],
    )
    op.alter_column(
        "assignment", "resource_link_id", existing_type=sa.VARCHAR(), nullable=True
    )
    op.create_check_constraint(
        "nullable_resource_link_id_ext_lti_assignment_id",
        table_name="assignment",
        condition="NOT(resource_link_id IS NULL AND ext_lti_assignment_id IS NULL)",
    )
