"""Add the user_preferences table.

Revision ID: 74318dc2de37
Revises: 14e959ea6f99
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "74318dc2de37"
down_revision = "14e959ea6f99"


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("h_userid", sa.Unicode(), nullable=False),
        sa.Column(
            "preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__user_preferences")),
        sa.UniqueConstraint("h_userid", name=op.f("uq__user_preferences__h_userid")),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
