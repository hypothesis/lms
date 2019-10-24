"""
Add the oauth2_unvalidated_credentials table.

Revision ID: f013a6b67f91
Revises: None
Create Date: 2017-08-16 16:49:03.696908

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f013a6b67f91"
down_revision = None


def upgrade():
    op.create_table(
        "oauth2_unvalidated_credentials",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("client_id", sa.UnicodeText),
        sa.Column("client_secret", sa.UnicodeText),
        sa.Column("authorization_server", sa.UnicodeText),
        sa.Column("email_address", sa.UnicodeText),
    )


def downgrade():
    op.drop_table("oauth2_unvalidated_credentials")
