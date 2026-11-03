"""Add hubspot_company.current_deal_users_contracted.

Revision ID: 8e86cab53a38
Revises: 1103b3072f9e
"""

import sqlalchemy as sa
from alembic import op

revision = "8e86cab53a38"
down_revision = "1103b3072f9e"


def upgrade() -> None:
    # Nullable with no backfill: the value is populated by the next
    # refresh_hubspot_data run (13:00 UTC daily), and stays NULL for the
    # companies HubSpot has no current deal for -- which is most of them.
    op.add_column(
        "hubspot_company",
        sa.Column("current_deal_users_contracted", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("hubspot_company", "current_deal_users_contracted")
