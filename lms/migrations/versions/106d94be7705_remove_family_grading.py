"""
Remove tool_consumer_info_product_family_code from GradingInfo.

Revision ID: 106d94be7705
Revises: 973c9358b616
Create Date: 2023-07-06 11:23:10.850486

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "106d94be7705"
down_revision = "973c9358b616"


def upgrade():
    op.drop_column("lis_result_sourcedid", "tool_consumer_info_product_family_code")


def downgrade():
    op.add_column(
        "lis_result_sourcedid",
        sa.Column(
            "tool_consumer_info_product_family_code",
            sa.TEXT(),
            autoincrement=False,
            nullable=True,
        ),
    )
