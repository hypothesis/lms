"""
Add group_info table.

Revision ID: a930adadac74
Revises: edab0e4610e0
Create Date: 2019-10-30 19:13:40.045469

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a930adadac74"
down_revision = "d54c5430ea36"


def upgrade():
    op.create_table(
        "group_info",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "authority_provided_id", sa.UnicodeText(), nullable=False, unique=True
        ),
        sa.Column(
            "consumer_key",
            sa.String(),
            sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
            nullable=False,
        ),
        sa.Column("context_id", sa.UnicodeText()),
        sa.Column("context_title", sa.UnicodeText()),
        sa.Column("context_label", sa.UnicodeText()),
        sa.Column("tool_consumer_info_product_family_code", sa.UnicodeText()),
        sa.Column("tool_consumer_info_version", sa.UnicodeText()),
        sa.Column("tool_consumer_instance_name", sa.UnicodeText()),
        sa.Column("tool_consumer_instance_description", sa.UnicodeText()),
        sa.Column("tool_consumer_instance_url", sa.UnicodeText()),
        sa.Column("tool_consumer_instance_contact_email", sa.UnicodeText()),
        sa.Column("tool_consumer_instance_guid", sa.UnicodeText()),
        sa.Column("custom_canvas_api_domain", sa.UnicodeText()),
        sa.Column("custom_canvas_course_id", sa.UnicodeText()),
    )


def downgrade():
    op.drop_table("group_info")
