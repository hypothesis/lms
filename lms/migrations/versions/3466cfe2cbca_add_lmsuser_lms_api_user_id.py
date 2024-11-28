"""Add LMSUser.lms_api_user_id."""

import sqlalchemy as sa
from alembic import op

revision = "3466cfe2cbca"
down_revision = "50fb51c51314"


def upgrade() -> None:
    op.add_column("lms_user", sa.Column("lms_api_user_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("lms_user", "lms_api_user_id")
