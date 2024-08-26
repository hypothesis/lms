"""Add LMSCourse.lti_context_memberships_url."""

import sqlalchemy as sa
from alembic import op

revision = "b97080de93bc"
down_revision = "aef6a6460d0d"


def upgrade() -> None:
    op.add_column(
        "lms_course",
        sa.Column("lti_context_memberships_url", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lms_course", "lti_context_memberships_url")
