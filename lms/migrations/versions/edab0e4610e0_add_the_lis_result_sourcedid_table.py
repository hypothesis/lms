"""
Add the lis_result_sourcedid table.

This table allows us to stash Learner launch-parameter details for later use
during grading

Revision ID: edab0e4610e0
Revises: 2fdc9b46320a
Create Date: 2019-09-05 14:15:47.918403

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "edab0e4610e0"
down_revision = "2fdc9b46320a"


def upgrade():
    op.create_table(
        "lis_result_sourcedid",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "created",
            sa.DateTime(),
            default=datetime.datetime.utcnow,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated",
            sa.DateTime(),
            server_default=sa.func.now(),
            default=datetime.datetime.utcnow,
            onupdate=datetime.datetime.utcnow,
            nullable=False,
        ),
        sa.Column("lis_result_sourcedid", sa.UnicodeText(), nullable=False),
        sa.Column("lis_outcome_service_url", sa.UnicodeText(), nullable=False),
        sa.Column("lis_result_sourcedid", sa.UnicodeText(), nullable=False),
        sa.Column(
            "oauth_consumer_key",
            sa.UnicodeText(),
            sa.ForeignKey("application_instances.consumer_key"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UnicodeText(), nullable=False),
        sa.Column("context_id", sa.UnicodeText(), nullable=False),
        sa.Column("resource_link_id", sa.UnicodeText(), nullable=False),
        sa.Column(
            "tool_consumer_info_product_family_code", sa.UnicodeText(), nullable=True
        ),
        sa.Column("h_username", sa.UnicodeText(), nullable=False),
        sa.Column("h_display_name", sa.UnicodeText(), nullable=False),
        sa.UniqueConstraint(
            "oauth_consumer_key", "user_id", "context_id", "resource_link_id"
        ),
    )


def downgrade():
    op.drop_table("lis_result_sourcedid")
