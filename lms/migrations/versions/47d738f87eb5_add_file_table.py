"""
Add file table.

Revision ID: 47d738f87eb5
Revises: bb11b5b06274
Create Date: 2021-06-15 13:44:45.368126

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "47d738f87eb5"
down_revision = "bb11b5b06274"


def upgrade():
    op.create_table(
        "file",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_instance_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.UnicodeText(), nullable=False),
        sa.Column("lms_id", sa.UnicodeText(), nullable=False),
        sa.Column("course_id", sa.UnicodeText(), nullable=True),
        sa.Column("name", sa.UnicodeText(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_instance_id"],
            ["application_instances.id"],
            name=op.f("fk__file__application_instance_id__application_instances"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__file")),
        sa.UniqueConstraint(
            "application_instance_id",
            "lms_id",
            "type",
            "course_id",
            name=op.f("uq__file__application_instance_id"),
        ),
    )


def downgrade():
    op.drop_table("file")
