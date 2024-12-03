"""
Enable email digest (batch 02).

Revision ID: 088813d3e6f8
Revises: b11713314988
Create Date: 2023-05-19 10:19:54.691419

"""

from alembic import op

from lms.migrations.versions.b11713314988_email_digest_enable_01 import (
    enable_email_digest,
)

revision = "088813d3e6f8"
down_revision = "b11713314988"


def upgrade():
    conn = op.get_bind()
    enable_email_digest(conn, 1000)


def downgrade():
    """No downgrade section as we might manually change some values after running `upgrade`."""
    pass
