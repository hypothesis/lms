"""Remove the email_unsubscribe table.

Revision ID: 522985f4fa6e
Revises: 68f4e83eec70
"""

from alembic import op

revision = "522985f4fa6e"
down_revision = "68f4e83eec70"


def upgrade() -> None:
    op.drop_table("email_unsubscribe")


def downgrade() -> None:
    pass
