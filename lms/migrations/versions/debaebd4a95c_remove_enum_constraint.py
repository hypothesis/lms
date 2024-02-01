"""
Remove enum DB constraint.

Revision ID: debaebd4a95c
Revises: 0b7391f5b1e3
Create Date: 2022-12-27 14:19:35.278944

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "debaebd4a95c"
down_revision = "0b7391f5b1e3"

constraint_name = "grouping_type_must_be_a_valid_value"
table_name = "grouping"


def upgrade():
    op.drop_constraint(constraint_name, table_name=table_name, type_="check")


def downgrade():
    op.create_check_constraint(
        constraint_name,
        table_name=table_name,
        condition="type in ('course', 'canvas_section', 'canvas_group', 'blackboard_group', 'd2l_group')",
    )
