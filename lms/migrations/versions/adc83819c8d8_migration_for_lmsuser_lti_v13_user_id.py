"""Migration for LMSUser.lti_v13_user_id."""

import sqlalchemy as sa
from alembic import op

revision = "adc83819c8d8"
down_revision = "f521d69a47d2"


def upgrade() -> None:
    op.add_column("lms_user", sa.Column("lti_v13_user_id", sa.Unicode(), nullable=True))


def downgrade() -> None:
    op.drop_column("lms_user", "lti_v13_user_id")
