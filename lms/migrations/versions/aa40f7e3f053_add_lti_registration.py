"""
Create lti_registration.

Revision ID: aa40f7e3f053
Revises: 0a3bfcc14133
Create Date: 2022-03-17 11:33:52.487641

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "aa40f7e3f053"
down_revision = "0a3bfcc14133"


def upgrade():
    op.create_table(
        "lti_registration",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("issuer", sa.UnicodeText(), nullable=False),
        sa.Column("client_id", sa.UnicodeText(), nullable=False),
        sa.Column("auth_login_url", sa.UnicodeText(), nullable=False),
        sa.Column("key_set_url", sa.UnicodeText(), nullable=False),
        sa.Column("token_url", sa.UnicodeText(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lti_registration")),
        sa.UniqueConstraint(
            "issuer", "client_id", name=op.f("uq__lti_registration__issuer")
        ),
    )


def downgrade():
    op.drop_table("lti_registration")
