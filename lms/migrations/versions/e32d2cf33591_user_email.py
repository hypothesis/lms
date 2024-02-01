"""
Add "email" and "display_name" to the user table.

Revision ID: e32d2cf33591
Revises: f8b1ac3ca221
Create Date: 2022-12-19 10:35:05.433945

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e32d2cf33591"
down_revision = "c14193c4afb4"


def upgrade():
    op.add_column("user", sa.Column("email", sa.Unicode(), nullable=True))
    op.add_column("user", sa.Column("display_name", sa.Unicode(), nullable=True))


def downgrade():
    op.drop_column("user", "email")
    op.drop_column("user", "display_name")
