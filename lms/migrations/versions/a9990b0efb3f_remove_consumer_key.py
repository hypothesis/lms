"""
Remove unused consumer_key columns.

Revision ID: a9990b0efb3f
Revises: 1e146996cca6
Create Date: 2022-07-11 12:28:13.684023

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a9990b0efb3f"
down_revision = "1e146996cca6"


def upgrade():
    op.drop_column("group_info", "consumer_key")
    op.drop_column("lis_result_sourcedid", "oauth_consumer_key")
    op.drop_column("oauth2_token", "consumer_key")


def downgrade():
    op.add_column(
        "oauth2_token",
        sa.Column("consumer_key", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "lis_result_sourcedid",
        sa.Column("oauth_consumer_key", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "group_info",
        sa.Column("consumer_key", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
