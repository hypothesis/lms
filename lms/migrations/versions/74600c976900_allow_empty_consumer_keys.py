"""
allow_empty_consumer_keys

Revision ID: 74600c976900
Revises: 7a4812876915
Create Date: 2022-02-11 10:36:40.960580

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "74600c976900"
down_revision = "7a4812876915"


def upgrade():
    op.alter_column(
        "application_instances",
        "consumer_key",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "application_instances",
        "consumer_key",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
