"""
New d2l_group type for groupings.

Revision ID: 6eb9de301ac3
Revises: 52755322151e
Create Date: 2022-11-17 11:28:55.747286

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6eb9de301ac3"
down_revision = "52755322151e"

constraint_name = "grouping_type_must_be_a_valid_value"
table_name = "grouping"


def upgrade():
    op.drop_constraint(constraint_name, table_name=table_name, type_="check")
    op.create_check_constraint(
        constraint_name,
        table_name=table_name,
        condition="type in ('course', 'canvas_section', 'canvas_group', 'blackboard_group', 'd2l_group')",
    )


def downgrade():
    op.drop_constraint(constraint_name, table_name=table_name, type_="check")
    op.create_check_constraint(
        constraint_name,
        table_name=table_name,
        condition="type in ('course', 'canvas_section', 'canvas_group', 'blackboard_group')",
    )
