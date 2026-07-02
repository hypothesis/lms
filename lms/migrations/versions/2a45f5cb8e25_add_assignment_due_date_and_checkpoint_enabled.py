"""Add assignment due_date and checkpoint_enabled columns.

Revision ID: 2a45f5cb8e25
Revises: b91594c0e379
"""

import sqlalchemy as sa
from alembic import op

revision = "2a45f5cb8e25"
down_revision = "b91594c0e379"


def upgrade() -> None:
    op.add_column("assignment", sa.Column("due_date", sa.DateTime(), nullable=True))
    op.add_column(
        "assignment",
        sa.Column(
            "checkpoint_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("assignment", "checkpoint_enabled")
    op.drop_column("assignment", "due_date")
