"""
Add oauth2_token table.

Revision ID: f36f9a0aadf4
Revises: 7000bb8673c5
Create Date: 2019-05-15 13:26:41.905098

"""
from alembic import op
import sqlalchemy as sa

revision = "f36f9a0aadf4"
down_revision = "7000bb8673c5"


def upgrade():
    op.create_table(
        "oauth2_token",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.UnicodeText(), nullable=False),
        sa.Column(
            "consumer_key",
            sa.String(),
            sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
            nullable=False,
        ),
        sa.Column("access_token", sa.UnicodeText(), nullable=False),
        sa.Column("refresh_token", sa.UnicodeText()),
        sa.Column("expires_in", sa.Integer()),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "user_id", "consumer_key", name="uq__oauth2_token__user_id"
        ),
    )


def downgrade():
    op.drop_table("oauth2_token")
