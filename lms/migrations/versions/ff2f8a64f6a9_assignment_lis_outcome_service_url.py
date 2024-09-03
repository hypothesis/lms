"""Add the Assignment.lis_outcome_service_url column."""

import sqlalchemy as sa
from alembic import op

revision = "ff2f8a64f6a9"
down_revision = "cb5fe6e8dc09"


def upgrade() -> None:
    op.add_column(
        "assignment", sa.Column("lis_outcome_service_url", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("assignment", "lis_outcome_service_url")
