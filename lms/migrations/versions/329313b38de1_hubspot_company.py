"""Create hubspot_company table."""

import sqlalchemy as sa
from alembic import op

revision = "329313b38de1"
down_revision = "7ef5569fca11"


def upgrade() -> None:
    op.create_table(
        "hubspot_company",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hubspot_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("lms_organization_id", sa.String(), nullable=True),
        sa.Column("current_deal_services_start", sa.Date(), nullable=True),
        sa.Column("current_deal_services_end", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__hubspot_company")),
        sa.UniqueConstraint("hubspot_id", name=op.f("uq__hubspot_company__hubspot_id")),
    )


def downgrade() -> None:
    op.drop_table("hubspot_company")
