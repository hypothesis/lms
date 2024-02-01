"""
Add a default to application instance create.

Revision ID: d737e73915b8
Revises: 64fd59a9f4b6
Create Date: 2023-02-09 13:20:08.536676

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d737e73915b8"
down_revision = "64fd59a9f4b6"


def upgrade():
    op.alter_column("application_instances", "created", server_default=sa.func.now())


def downgrade():
    op.alter_column("application_instances", "created", server_default=None)
