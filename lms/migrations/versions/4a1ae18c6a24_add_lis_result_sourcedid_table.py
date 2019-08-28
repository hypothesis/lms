"""
Add the lis_result_sourcedid table.

Revision ID: 4a1ae18c6a24
Revises: 2fdc9b46320a
Create Date: 2019-08-28 11:27:18.907792

"""
from alembic import op
import sqlalchemy as sa


revision = "4a1ae18c6a24"
down_revision = "2fdc9b46320a"


def upgrade():
    op.create_table(
        "lis_result_sourcedid",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("lis_result_sourcedid", sa.UnicodeText(), nullable=False),
        sa.Column("lis_outcome_service_url", sa.UnicodeText(), nullable=False),
        sa.Column("oauth_consumer_key", sa.UnicodeText(), nullable=False),
        sa.Column("user_id", sa.UnicodeText(), nullable=False),
        sa.Column("context_id", sa.UnicodeText(), nullable=False),
        sa.Column("resource_link_id", sa.UnicodeText(), nullable=False),
        sa.Column("username", sa.UnicodeText(), nullable=False),
        sa.Column("display_name", sa.UnicodeText(), nullable=False),
        sa.UniqueConstraint(
            "oauth_consumer_key",
            "user_id",
            "context_id",
            "resource_link_id",
        ),
    )


def downgrade():
    op.drop_table("lis_result_sourcedid")
