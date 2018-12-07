"""
Add the provisioning column.

Revision ID: 7e4124035651
Revises: efcf8671f4d3
Create Date: 2018-12-07 11:38:55.717986

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7e4124035651"
down_revision = "efcf8671f4d3"


def upgrade():
    op.add_column(
        "application_instances",
        sa.Column(
            "provisioning",
            sa.Boolean(),
            server_default=sa.sql.expression.true(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("application_instances", "provisioning")
