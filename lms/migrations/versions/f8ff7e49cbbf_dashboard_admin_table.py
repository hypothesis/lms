"""Create the dashboard_admin table.

Revision ID: f8ff7e49cbbf
Revises: 8e203ad93a58
"""

import sqlalchemy as sa
from alembic import op

revision = "f8ff7e49cbbf"

down_revision = "1337584e2b07"


def upgrade() -> None:
    op.create_table(
        "dashboard_admin",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk__dashboard_admin__organization_id__organization"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__dashboard_admin")),
        sa.UniqueConstraint(
            "organization_id",
            "email",
            name=op.f("uq__dashboard_admin__organization_id"),
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table("dashboard_admin")
