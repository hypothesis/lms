"""
Add assignment_grouping.

Revision ID: 1e146996cca6
Revises: fe80746cf145
Create Date: 2022-06-09 20:29:01.237582

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1e146996cca6"
down_revision = "fe80746cf145"


def upgrade():
    op.create_table(
        "assignment_grouping",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("grouping_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk__assignment_grouping__assignment_id__assignment"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["grouping_id"],
            ["grouping.id"],
            name=op.f("fk__assignment_grouping__grouping_id__grouping"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint(
            "assignment_id", "grouping_id", name=op.f("pk__assignment_grouping")
        ),
    )


def downgrade():
    op.drop_table("assignment_grouping")
