"""
add_lti_13_fields

Revision ID: e22fa595b11d
Revises: 74600c976900
Create Date: 2022-02-11 10:41:56.115951

"""
from alembic import op
import sqlalchemy as sa


revision = "e22fa595b11d"
down_revision = "74600c976900"


def upgrade():
    op.add_column(
        "application_instances", sa.Column("issuer", sa.UnicodeText(), nullable=True)
    )
    op.add_column(
        "application_instances", sa.Column("client_id", sa.UnicodeText(), nullable=True)
    )
    op.add_column(
        "application_instances",
        sa.Column("key_set_url", sa.UnicodeText(), nullable=True),
    )
    op.add_column(
        "application_instances",
        sa.Column("auth_login_url", sa.UnicodeText(), nullable=True),
    )
    op.add_column(
        "application_instances",
        sa.Column("deployment_id", sa.UnicodeText(), nullable=True),
    )


def downgrade():
    op.drop_column("application_instances", "auth_login_url")
    op.drop_column("application_instances", "key_set_url")
    op.drop_column("application_instances", "client_id")
    op.drop_column("application_instances", "issuer")
    op.drop_column("application_instances", "deployment_id")
