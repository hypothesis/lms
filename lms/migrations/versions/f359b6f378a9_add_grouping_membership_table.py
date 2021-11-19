"""
Adds grouping_membership table.

Revision ID: f359b6f378a9
Revises: 2fd66b9ab1a1
Create Date: 2021-11-23 14:59:33.455057

"""
import sqlalchemy as sa
from alembic import op

revision = "f359b6f378a9"
down_revision = "1693f6ade03d"


def upgrade():
    op.create_table(
        "grouping_membership",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("grouping_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["grouping_id"],
            ["grouping.id"],
            name=op.f("fk__grouping_membership__grouping_id__grouping"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__grouping_membership__user_id__user"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint(
            "grouping_id", "user_id", name=op.f("pk__grouping_membership")
        ),
    )


def downgrade():
    op.drop_table("grouping_membership")
