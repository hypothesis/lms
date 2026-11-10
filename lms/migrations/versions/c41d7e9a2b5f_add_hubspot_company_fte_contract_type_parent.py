"""Add hubspot_company.student_fte, contract_type and parent_hubspot_id.

Revision ID: c41d7e9a2b5f
Revises: 8e86cab53a38
"""

import sqlalchemy as sa
from alembic import op

revision = "c41d7e9a2b5f"
down_revision = "8e86cab53a38"


def upgrade() -> None:
    # Nullable with no backfill, like current_deal_users_contracted: the
    # values are populated by the next refresh_hubspot_data run.
    op.add_column(
        "hubspot_company", sa.Column("student_fte", sa.Integer(), nullable=True)
    )
    op.add_column(
        "hubspot_company", sa.Column("contract_type", sa.String(), nullable=True)
    )
    op.add_column(
        "hubspot_company",
        sa.Column("parent_hubspot_id", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("hubspot_company", "parent_hubspot_id")
    op.drop_column("hubspot_company", "contract_type")
    op.drop_column("hubspot_company", "student_fte")
