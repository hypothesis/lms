"""
Add LMS columns to the application_instances table.

Revision ID: 5f80062abcf4
Revises: 5086e8b137b9
Create Date: 2021-05-20 13:14:41.145891

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5f80062abcf4"
down_revision = "5086e8b137b9"


def upgrade():
    op.add_column(
        "application_instances",
        sa.Column("tool_consumer_instance_guid", sa.UnicodeText(), nullable=True),
    )
    op.add_column(
        "application_instances",
        sa.Column(
            "tool_consumer_info_product_family_code", sa.UnicodeText(), nullable=True
        ),
    )
    op.add_column(
        "application_instances",
        sa.Column(
            "tool_consumer_instance_description", sa.UnicodeText(), nullable=True
        ),
    )
    op.add_column(
        "application_instances",
        sa.Column("tool_consumer_instance_url", sa.UnicodeText(), nullable=True),
    )
    op.add_column(
        "application_instances",
        sa.Column("tool_consumer_instance_name", sa.UnicodeText(), nullable=True),
    )
    op.add_column(
        "application_instances",
        sa.Column(
            "tool_consumer_instance_contact_email", sa.UnicodeText(), nullable=True
        ),
    )
    op.add_column(
        "application_instances",
        sa.Column("tool_consumer_info_version", sa.UnicodeText(), nullable=True),
    )
    op.add_column(
        "application_instances",
        sa.Column("custom_canvas_api_domain", sa.UnicodeText(), nullable=True),
    )


def downgrade():
    op.drop_column("application_instances", "custom_canvas_api_domain")
    op.drop_column("application_instances", "tool_consumer_info_version")
    op.drop_column("application_instances", "tool_consumer_instance_contact_email")
    op.drop_column("application_instances", "tool_consumer_instance_name")
    op.drop_column("application_instances", "tool_consumer_instance_url")
    op.drop_column("application_instances", "tool_consumer_instance_description")
    op.drop_column("application_instances", "tool_consumer_info_product_family_code")
    op.drop_column("application_instances", "tool_consumer_instance_guid")
