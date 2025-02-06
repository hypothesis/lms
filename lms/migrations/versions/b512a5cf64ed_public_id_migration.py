"""Public ID migration.

Revision ID: b512a5cf64ed
Revises: 329313b38de1
"""

import os

import sqlalchemy as sa
from alembic import op

revision = "b512a5cf64ed"
down_revision = "329313b38de1"


def upgrade() -> None:
    region = os.environ["REGION_CODE"]
    conn = op.get_bind()
    conn.execute(
        sa.text(
            f"""UPDATE "organization" set public_id = '{region}.lms.org.' || "public_id";"""  # noqa: S608
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """UPDATE "organization" set public_id = split_part("public_id", '.', 4);"""
        )
    )
