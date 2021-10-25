"""
Add the "User" table.

Revision ID: 2fd66b9ab1a1
Revises: 490952a3fbe8
Create Date: 2021-10-25 18:38:09.045576

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2fd66b9ab1a1"
down_revision = "490952a3fbe8"


def upgrade():
    op.create_table(
        "user",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_instance_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Unicode(), nullable=False),
        sa.Column("roles", sa.Unicode(), nullable=True),
        sa.Column("h_userid", sa.Unicode(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_instance_id"],
            ["application_instances.id"],
            name=op.f("fk__user__application_instance_id__application_instances"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__user")),
        sa.UniqueConstraint(
            "application_instance_id",
            "user_id",
            "h_userid",
            name=op.f("uq__user__application_instance_id"),
        ),
    )


def downgrade():
    op.drop_table("user")
