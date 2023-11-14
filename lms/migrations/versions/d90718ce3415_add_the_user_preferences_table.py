"""Add the user_preferences table.

Revision ID: d90718ce3415
Revises: 0c52a13c6cad
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d90718ce3415"
down_revision = "0c52a13c6cad"


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
