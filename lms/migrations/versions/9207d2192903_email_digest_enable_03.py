"""
Enable email digest (batch 03).

Revision ID: 9207d2192903
Revises: 088813d3e6f8
Create Date: 2023-05-23 09:25:42.073245

"""

import sqlalchemy as sa
from alembic import op

from lms.migrations.versions.b11713314988_email_digest_enable_01 import (
    enable_email_digest,
)

revision = "9207d2192903"
down_revision = "088813d3e6f8"


def upgrade():
    conn = op.get_bind()
    enable_email_digest(conn, 40)


def downgrade():
    """No downgrade section as we might manually change some values after running `upgrade`."""
    pass
