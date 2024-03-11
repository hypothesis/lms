"""Add assignment.deep_linking_uuid."""

import sqlalchemy as sa
from alembic import op

revision = "7ef5569fca11"
down_revision = "c64961cf7254"


def upgrade() -> None:
    op.add_column(
        "assignment", sa.Column("deep_linking_uuid", sa.Unicode(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("assignment", "deep_linking_uuid")
