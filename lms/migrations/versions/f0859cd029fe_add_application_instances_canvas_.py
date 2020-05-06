"""
Add application_instances.canvas_sections_enabled column.

Revision ID: f0859cd029fe
Revises: 37710e6bcb66
Create Date: 2020-05-06 15:48:13.964730

"""
import sqlalchemy as sa
from alembic import op

revision = "f0859cd029fe"
down_revision = "37710e6bcb66"


def upgrade():
    op.add_column(
        "application_instances",
        sa.Column(
            "canvas_sections_enabled",
            sa.Boolean(),
            server_default=sa.sql.expression.false(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("application_instances", "canvas_sections_enabled")
