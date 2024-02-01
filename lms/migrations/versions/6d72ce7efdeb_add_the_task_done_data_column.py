"""Add the task_done.data column.

Revision ID: 6d72ce7efdeb
Revises: 74318dc2de37
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "6d72ce7efdeb"
down_revision = "74318dc2de37"


def upgrade() -> None:
    op.add_column(
        "task_done",
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("task_done", "data")
