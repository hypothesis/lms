"""Create the usage_report table.

Revision ID: 73f0011260e4
Revises: 329313b38de1
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "73f0011260e4"
down_revision = "329313b38de1"


def upgrade() -> None:
    op.create_table(
        "organization_usage_report",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("since", sa.Date(), nullable=True),
        sa.Column("until", sa.Date(), nullable=True),
        sa.Column("unique_users", sa.Integer(), nullable=True),
        sa.Column("report", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk__organization_usage_report__organization_id__organization"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__organization_usage_report")),
        sa.UniqueConstraint("key", name=op.f("uq__organization_usage_report__key")),
    )


def downgrade() -> None:
    op.drop_table("organization_usage_report")
