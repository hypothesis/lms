"""
Add ApplicationInstance.settings and Course.settings server defaults and make them not-nullable.

Revision ID: 5086e8b137b9
Revises: 7f9824ded172
Create Date: 2020-07-16 10:23:06.469812

"""
import sqlalchemy as sa
from alembic import op

revision = "5086e8b137b9"
down_revision = "7f9824ded172"


def upgrade():
    op.alter_column("application_instances", "settings", nullable=False)
    op.alter_column(
        "application_instances", "settings", server_default=sa.text("'{}'::jsonb")
    )
    op.alter_column("course", "settings", server_default=sa.text("'{}'::jsonb"))


def downgrade():
    op.alter_column("application_instances", "settings", nullable=True)
    op.alter_column("application_instances", "settings", server_default=None)
    op.alter_column("course", "settings", server_default=None)
