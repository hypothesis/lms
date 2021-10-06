"""
Use a wider integer type for file.size to account for files over 2GB.

Revision ID: 490952a3fbe8
Revises: d9c9e65c463e
Create Date: 2021-10-04 17:13:14.982895

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "490952a3fbe8"
down_revision = "d9c9e65c463e"


def upgrade():
    op.alter_column(
        "file",
        "size",
        existing_type=sa.INTEGER(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "file",
        "size",
        existing_type=sa.BigInteger(),
        type_=sa.INTEGER(),
        existing_nullable=True,
    )
