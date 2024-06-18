"""Add usage report teachers column.

Revision ID: da01fe01c324
Revises: 73f0011260e4
"""

import sqlalchemy as sa
from alembic import op

revision = "da01fe01c324"
down_revision = "73f0011260e4"


def upgrade() -> None:
    op.add_column(
        "organization_usage_report",
        sa.Column("unique_teachers", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("organization_usage_report", "unique_teachers")
