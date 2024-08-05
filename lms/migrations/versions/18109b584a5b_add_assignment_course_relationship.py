"""Add assignment course relationship."""

import sqlalchemy as sa
from alembic import op

revision = "18109b584a5b"
down_revision = "d8d33d882b88"


def upgrade() -> None:
    op.add_column("assignment", sa.Column("course_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk__assignment__course_id__grouping"),
        "assignment",
        "grouping",
        ["course_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk__assignment__course_id__grouping"), "assignment", type_="foreignkey"
    )
    op.drop_column("assignment", "course_id")
