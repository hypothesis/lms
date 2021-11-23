"""Add type column values constraint to grouping table."""
from alembic import op

revision = "6882c201b56e"
down_revision = "4a4c2539c666"

constraint_name = "grouping_type_must_be_a_valid_value"
table_name = "grouping"


def upgrade():
    op.create_check_constraint(
        constraint_name,
        table_name=table_name,
        condition="type in ('course', 'canvas_section', 'canvas_group', 'blackboard_group')",
    )


def downgrade():
    op.drop_constraint(constraint_name, table_name=table_name, type_="check")
