# -*- coding: utf-8 -*-
"""Add the course_groups table."""

from alembic import op
import sqlalchemy as sa


revision = "efcf8671f4d3"
down_revision = "64d9eacab937"


def upgrade():
    op.create_table(
        "course_groups",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("tool_consumer_instance_guid", sa.UnicodeText, nullable=False),
        sa.Column("context_id", sa.UnicodeText, nullable=False),
        sa.Column("pubid", sa.Text, nullable=False, unique=True),
    )
    op.create_index(
        index_name="ix__course_groups_tool_consumer_instance_guid_context_id",
        table_name="course_groups",
        columns=["tool_consumer_instance_guid", "context_id"],
        unique=True,
    )


def downgrade():
    op.drop_table("course_groups")
