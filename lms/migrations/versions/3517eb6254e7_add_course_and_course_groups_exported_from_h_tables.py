"""
Add the course table and course_groups_exported_from_h tables.

Revision ID: 3517eb6254e7
Revises: f0859cd029fe
Create Date: 2020-06-01 14:10:19.019286

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

revision = "3517eb6254e7"
down_revision = "f0859cd029fe"


def upgrade():
    op.create_table(
        "course",
        sa.Column(
            "consumer_key",
            sa.String(),
            sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
            primary_key=True,
        ),
        sa.Column("authority_provided_id", sa.UnicodeText(), primary_key=True),
        sa.Column("settings", MutableDict.as_mutable(JSONB), nullable=False),
    )

    op.create_table(
        "course_groups_exported_from_h",
        sa.Column("authority_provided_id", sa.UnicodeText(), primary_key=True,),
        sa.Column("created", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("course")
    op.drop_table("course_groups_exported_from_h")
