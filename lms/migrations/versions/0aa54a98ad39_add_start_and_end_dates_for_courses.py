"""Add start and end dates to courses."""

import sqlalchemy as sa
from alembic import op

revision = "0aa54a98ad39"
down_revision = "02d413b4d212"


def upgrade() -> None:
    op.add_column("lms_course", sa.Column("starts_at", sa.DateTime(), nullable=True))
    op.add_column("lms_course", sa.Column("ends_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("lms_course", "ends_at")
    op.drop_column("lms_course", "starts_at")
