"""
New rsa_key table.

Revision ID: 34f28d992b18
Revises: 497b20c41fbb
Create Date: 2022-04-21 11:08:09.946604

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "34f28d992b18"
down_revision = "497b20c41fbb"


def upgrade():
    op.create_table(
        "rsa_key",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("kid", sa.Unicode(), nullable=False),
        sa.Column("public_key", sa.Unicode(), nullable=True),
        sa.Column("private_key", sa.LargeBinary(), nullable=True),
        sa.Column("aes_cipher_iv", sa.LargeBinary(), nullable=True),
        sa.Column(
            "expired", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__rsa_key")),
    )


def downgrade():
    op.drop_table("rsa_key")
