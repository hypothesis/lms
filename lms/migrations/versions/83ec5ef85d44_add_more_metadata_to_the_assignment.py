"""
Add more metadata to the assignment.

Revision ID: 83ec5ef85d44
Revises: 52ff45973d5b
Create Date: 2022-06-08 14:27:26.384509

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "83ec5ef85d44"
down_revision = "52ff45973d5b"


def upgrade():
    op.add_column(
        "assignment",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.add_column(
        "assignment",
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.add_column(
        "assignment",
        sa.Column(
            "is_gradable", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column("assignment", sa.Column("title", sa.Unicode(), nullable=True))
    op.add_column("assignment", sa.Column("description", sa.Unicode(), nullable=True))
    # Use some magic values for exising rows so we can tell that these were
    # created prior to this update
    op.execute("UPDATE assignment SET created='2000-01-01', updated='2000-01-01'")


def downgrade():
    op.drop_column("assignment", "description")
    op.drop_column("assignment", "title")
    op.drop_column("assignment", "is_gradable")
    op.drop_column("assignment", "updated")
    op.drop_column("assignment", "created")
