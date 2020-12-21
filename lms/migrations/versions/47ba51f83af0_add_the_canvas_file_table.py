"""
Add the canvas_file table.

Revision ID: 47ba51f83af0
Revises: 5086e8b137b9
Create Date: 2020-12-21 18:00:54.368084

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList

revision = "47ba51f83af0"
down_revision = "5086e8b137b9"


def upgrade():
    op.create_table(
        "canvas_file",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "consumer_key",
            sa.String,
            sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
            nullable=False,
        ),
        sa.Column("tool_consumer_instance_guid", sa.UnicodeText, nullable=False),
        sa.Column("file_id", sa.Integer, nullable=False),
        sa.Column("course_id", sa.Integer, nullable=False),
        sa.Column("filename", sa.UnicodeText, nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column(
            "file_id_history",
            MutableList.as_mutable(ARRAY(sa.Integer)),
            server_default="{}",
            nullable=False,
        ),
        sa.UniqueConstraint("consumer_key", "tool_consumer_instance_guid", "file_id"),
    )


def downgrade():
    op.drop_table("canvas_file")
