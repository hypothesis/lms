"""New LMSUser name columns."""

import sqlalchemy as sa
from alembic import op

revision = "833f6b0237d8"
down_revision = "0d265909ff85"


def upgrade() -> None:
    op.add_column("lms_user", sa.Column("given_name", sa.String(), nullable=True))
    op.add_column("lms_user", sa.Column("family_name", sa.String(), nullable=True))
    op.add_column("lms_user", sa.Column("name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("lms_user", "name")
    op.drop_column("lms_user", "family_name")
    op.drop_column("lms_user", "given_name")
