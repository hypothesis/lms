"""
Add copied_from_id to assignment.

Revision ID: 5f0057d6d60f
Revises: d737e73915b8
Create Date: 2023-02-20 09:33:35.423402

"""

import sqlalchemy as sa
from alembic import op

revision = "5f0057d6d60f"
down_revision = "d737e73915b8"


def upgrade():
    op.add_column(
        "assignment", sa.Column("copied_from_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk__assignment__copied_from_id__assignment"),
        "assignment",
        "assignment",
        ["copied_from_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__assignment__copied_from_id__assignment"),
        "assignment",
        type_="foreignkey",
    )
    op.drop_column("assignment", "copied_from_id")
