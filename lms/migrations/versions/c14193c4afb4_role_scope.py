"""
Add the scope column to "lti_role".

Revision ID: c14193c4afb4
Revises: 6eb9de301ac3
Create Date: 2022-12-08 15:33:11.055578

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c14193c4afb4"
down_revision = "6eb9de301ac3"


def upgrade():
    op.add_column(
        "lti_role",
        sa.Column(
            "scope",
            sa.Enum(
                "course",
                "institution",
                "system",
                name="rolescope",
                native_enum=False,
                length=64,
            ),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("lti_role", "scope")
