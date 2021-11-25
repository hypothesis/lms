"""
Constrain child groupings to belong to their parent's application instance.

Revision ID: f581d8a273cc
Revises: 6882c201b56e
Create Date: 2022-01-25 17:57:55.813338

"""
import sqlalchemy as sa
from alembic import op

revision = "f581d8a273cc"
down_revision = "6882c201b56e"


def upgrade():
    op.drop_constraint(
        "fk__grouping__parent_id__grouping", "grouping", type_="foreignkey"
    )
    op.create_unique_constraint(
        op.f("uq__grouping__id"), "grouping", ["id", "application_instance_id"]
    )
    op.create_foreign_key(
        op.f("fk__grouping__parent_id__grouping"),
        "grouping",
        "grouping",
        ["parent_id", "application_instance_id"],
        ["id", "application_instance_id"],
        ondelete="cascade",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__grouping__parent_id__grouping"), "grouping", type_="foreignkey"
    )
    op.drop_constraint(op.f("uq__grouping__id"), "grouping", type_="unique")
    op.create_foreign_key(
        "fk__grouping__parent_id__grouping",
        "grouping",
        "grouping",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )
