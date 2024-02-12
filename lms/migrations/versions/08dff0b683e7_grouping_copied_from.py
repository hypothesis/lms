"""Add copied from ID to groupings."""

import sqlalchemy as sa
from alembic import op

revision = "08dff0b683e7"
down_revision = "522985f4fa6e"


def upgrade() -> None:
    op.add_column("grouping", sa.Column("copied_from_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk__grouping__copied_from_id__grouping"),
        "grouping",
        "grouping",
        ["copied_from_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk__grouping__copied_from_id__grouping"), "grouping", type_="foreignkey"
    )
    op.drop_column("grouping", "copied_from_id")
