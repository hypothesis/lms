"""
Add the email_unsubscribe table.

Revision ID: 9f1e88367596
Revises: f3d631c110bf
Create Date: 2023-04-06 14:44:40.077112

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f1e88367596"
down_revision = "f3d631c110bf"


def upgrade():
    op.create_table(
        "email_unsubscribe",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tag", sa.UnicodeText(), nullable=False),
        sa.Column("h_userid", sa.Unicode(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__email_unsubscribe")),
        sa.UniqueConstraint(
            "h_userid", "tag", name=op.f("uq__email_unsubscribe__h_userid")
        ),
    )


def downgrade():
    op.drop_table("email_unsubscribe")
