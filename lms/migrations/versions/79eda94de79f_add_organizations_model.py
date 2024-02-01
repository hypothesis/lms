"""
Add Organizations model.

Revision ID: 79eda94de79f
Revises: 396f46318023
Create Date: 2022-09-07 16:57:14.077132

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "79eda94de79f"
down_revision = "9bb2beba95bc"


def upgrade():
    op.create_table(
        "organization",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.UnicodeText(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("public_id", sa.UnicodeText(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["organization.id"],
            name=op.f("fk__organization__parent_id__organization"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__organization")),
        sa.UniqueConstraint("public_id", name=op.f("uq__organization__public_id")),
    )

    op.add_column(
        "application_instances",
        sa.Column("organization_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk__application_instances__organization_id__organization"),
        "application_instances",
        "organization",
        ["organization_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__application_instances__organization_id__organization"),
        "application_instances",
        type_="foreignkey",
    )
    op.drop_column("application_instances", "organization_id")

    op.drop_table("organization")
