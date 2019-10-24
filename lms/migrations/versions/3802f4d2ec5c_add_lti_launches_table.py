"""
Add lti_launches table.

Revision ID: 3802f4d2ec5c
Revises: 58f2693de313
Create Date: 2017-12-11 14:21:53.686455

"""
from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3802f4d2ec5c"
down_revision = "58f2693de313"


def upgrade():
    op.create_table(
        "lti_launches",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("created", sa.TIMESTAMP, default=datetime.utcnow),
        sa.Column("context_id", sa.String),
        sa.Column("lti_key", sa.String),
    )


def downgrade():
    op.drop_table("lti_launches")
