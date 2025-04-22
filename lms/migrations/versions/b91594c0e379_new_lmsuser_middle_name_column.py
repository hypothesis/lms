"""New LMSUser middle_name column."""

import sqlalchemy as sa
from alembic import op

revision = "b91594c0e379"
down_revision = "833f6b0237d8"


def upgrade() -> None:
    op.add_column("lms_user", sa.Column("middle_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("lms_user", "middle_name")
