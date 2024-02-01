"""
Create the jwt_token_table.

Revision ID: 973c9358b616
Revises: 3a786e91f59c
Create Date: 2023-06-02 12:04:16.991157

"""

import sqlalchemy as sa
from alembic import op

revision = "973c9358b616"
down_revision = "3a786e91f59c"


def upgrade():
    op.create_table(
        "jwt_oauth2_token",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("lti_registration_id", sa.Integer(), nullable=False),
        sa.Column("scopes", sa.UnicodeText(), nullable=False),
        sa.Column("access_token", sa.UnicodeText(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lti_registration_id"],
            ["lti_registration.id"],
            name=op.f("fk__jwt_oauth2_token__lti_registration_id__lti_registration"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__jwt_oauth2_token")),
        sa.UniqueConstraint(
            "lti_registration_id",
            "scopes",
            name=op.f("uq__jwt_oauth2_token__lti_registration_id"),
        ),
    )


def downgrade():
    op.drop_table("jwt_oauth2_token")
