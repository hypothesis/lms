"""Assignment v13 ID."""

import sqlalchemy as sa
from alembic import op

revision = "481968561169"
down_revision = "9e79650bed37"


def upgrade() -> None:
    op.add_column(
        "assignment", sa.Column("lti_v13_resource_link_id", sa.Unicode(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("assignment", "lti_v13_resource_link_id")
