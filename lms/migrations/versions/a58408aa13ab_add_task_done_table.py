"""
Add task_done table.

Revision ID: a58408aa13ab
Revises: 9f1e88367596
Create Date: 2023-05-01 10:37:08.209572

"""

from alembic import op
from sqlalchemy import Column, DateTime, Integer, UnicodeText, func, text

revision = "a58408aa13ab"
down_revision = "9f1e88367596"


def upgrade():
    op.create_table(
        "task_done",
        Column("created", DateTime, server_default=func.now(), nullable=False),
        Column(
            "updated",
            DateTime,
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        Column("id", Integer, autoincrement=True, primary_key=True),
        Column("key", UnicodeText, nullable=False, unique=True),
        Column(
            "expires_at",
            DateTime,
            nullable=False,
            server_default=text("now() + interval '30 days'"),
        ),
    )


def downgrade():
    op.drop_table("task_done")
