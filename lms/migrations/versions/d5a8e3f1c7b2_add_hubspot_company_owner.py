"""Add hubspot_company.owner_hubspot_id and owner_name.

Revision ID: d5a8e3f1c7b2
Revises: c41d7e9a2b5f
"""

import sqlalchemy as sa
from alembic import op

revision = "d5a8e3f1c7b2"
down_revision = "c41d7e9a2b5f"


def upgrade() -> None:
    # Nullable with no backfill, like the other mirrored HubSpot properties:
    # the values are populated by the next refresh_hubspot_data run.
    op.add_column(
        "hubspot_company",
        sa.Column("owner_hubspot_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "hubspot_company", sa.Column("owner_name", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("hubspot_company", "owner_name")
    op.drop_column("hubspot_company", "owner_hubspot_id")
