"""
keys

Revision ID: 5e029d1d99f9
Revises: c9ebaebb3eca
Create Date: 2022-02-25 10:23:28.897387

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5e029d1d99f9"
down_revision = "c9ebaebb3eca"


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "key",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("kid", postgresql.UUID(), nullable=False),
        sa.Column("aes_cipher_iv", sa.LargeBinary(), nullable=True),
        sa.Column("public_key", sa.Unicode(), nullable=True),
        sa.Column("_private_key", sa.LargeBinary(), nullable=True),
        sa.Column(
            "expired", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__key")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("key")
    # ### end Alembic commands ###
