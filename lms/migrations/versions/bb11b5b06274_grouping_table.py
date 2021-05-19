"""
Adds new grouping table.

Revision ID: bb11b5b06274
Revises: 5f80062abcf4
Create Date: 2021-05-19 11:11:39.560969

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bb11b5b06274"
down_revision = "5f80062abcf4"


def upgrade():
    op.create_table(
        "grouping",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_instance_id", sa.Integer(), nullable=False),
        sa.Column("authority_provided_id", sa.UnicodeText(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("lms_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("lms_name", sa.UnicodeText(), nullable=False),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "extra",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_instance_id"],
            ["application_instances.id"],
            name=op.f("fk__grouping__application_instance_id__application_instances"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["grouping.id"],
            name=op.f("fk__grouping__parent_id__grouping"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__grouping")),
        sa.UniqueConstraint(
            "application_instance_id",
            "authority_provided_id",
            name=op.f("uq__grouping__application_instance_id"),
        ),
    )


def downgrade():
    op.drop_table("grouping")
