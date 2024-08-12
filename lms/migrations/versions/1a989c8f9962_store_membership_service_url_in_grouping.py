"""Store memberhip service URL in grouping."""

import sqlalchemy as sa
from alembic import op

revision = "1a989c8f9962"
down_revision = "1b52e0668e7c"


def upgrade() -> None:
    op.add_column(
        "grouping",
        sa.Column("lti_context_memberships_url", sa.UnicodeText(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("grouping", "lti_context_memberships_url")
