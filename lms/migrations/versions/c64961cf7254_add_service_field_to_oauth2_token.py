"""Add `service` field to oauth2_token.

Revision ID: c64961cf7254
Revises: 08dff0b683e7
"""

import sqlalchemy as sa
from alembic import op

revision = "c64961cf7254"
down_revision = "08dff0b683e7"


def upgrade() -> None:
    op.add_column(
        "oauth2_token",
        sa.Column(
            "service",
            sa.Enum(
                "lms",
                "canvas_studio",
                name="service",
                native_enum=False,
                length=64,
            ),
            nullable=False,
            server_default=sa.text("'lms'"),
        ),
    )
    op.drop_constraint("uq__oauth2_token__user_id", "oauth2_token")
    op.create_unique_constraint(
        "uq__oauth2_token__user_id",
        "oauth2_token",
        ["user_id", "application_instance_id", "service"],
    )


def downgrade() -> None:
    op.drop_constraint("uq__oauth2_token__user_id", "oauth2_token")
    op.create_unique_constraint(
        "uq__oauth2_token__user_id",
        "oauth2_token",
        ["user_id", "application_instance_id"],
    )
    op.drop_column("oauth2_token", "service")
