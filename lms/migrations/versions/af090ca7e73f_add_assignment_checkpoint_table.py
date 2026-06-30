"""Add assignment_checkpoint table."""

import sqlalchemy as sa
from alembic import op

revision = "af090ca7e73f"
down_revision = "b91594c0e379"


def upgrade() -> None:
    op.create_table(
        "assignment_checkpoint",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("reveal_date", sa.DateTime(), nullable=True),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk__assignment_checkpoint__assignment_id__assignment"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__assignment_checkpoint")),
    )
    op.create_index(
        op.f("ix__assignment_checkpoint_assignment_id"),
        "assignment_checkpoint",
        ["assignment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix__assignment_checkpoint_assignment_id"),
        table_name="assignment_checkpoint",
    )
    op.drop_table("assignment_checkpoint")
