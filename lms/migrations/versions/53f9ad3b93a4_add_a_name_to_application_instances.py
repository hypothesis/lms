"""
Add a name to application instances.

Revision ID: 53f9ad3b93a4
Revises: debaebd4a95c
Create Date: 2023-01-24 17:48:15.688227

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "53f9ad3b93a4"
down_revision = "debaebd4a95c"


def upgrade():
    op.add_column(
        "application_instances", sa.Column("name", sa.UnicodeText(), nullable=True)
    )


def downgrade():
    op.drop_column("application_instances", "name")
