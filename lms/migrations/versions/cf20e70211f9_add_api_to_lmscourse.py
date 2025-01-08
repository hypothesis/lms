"""Add API ID to LMSCourse."""

import sqlalchemy as sa
from alembic import op

revision = "cf20e70211f9"
down_revision = "0aa54a98ad39"


def upgrade() -> None:
    op.add_column(
        "lms_course", sa.Column("lms_api_course_id", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("lms_course", "lms_api_course_id")
