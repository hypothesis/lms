"""Add checkpoint_enabled column to assignment.

Revision ID: c1a2b3d4e5f6
Revises: 2a45f5cb8e25
"""

import sqlalchemy as sa
from alembic import op

revision = "c1a2b3d4e5f6"
down_revision = "2a45f5cb8e25"


def upgrade() -> None:
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
