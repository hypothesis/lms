"""
Fix user_id unique constraint.

Revision ID: 7a4812876915
Revises: 6882c201b56e
Create Date: 2022-01-25 16:07:34.805966

"""
import sqlalchemy as sa
from alembic import op

revision = "7a4812876915"
down_revision = "f581d8a273cc"


def upgrade():
    op.drop_constraint("uq__user__application_instance_id", "user")

    op.create_unique_constraint(
        "uq__user__application_instance_id__user_id",
        "user",
        ["application_instance_id", "user_id"],
    )
    op.create_unique_constraint(
        "uq__user__application_instance_id__h_userid",
        "user",
        ["application_instance_id", "h_userid"],
    )


def downgrade():
    op.drop_constraint("uq__user__application_instance_id__user_id", "user")
    op.drop_constraint("uq__user__application_instance_id__h_userid", "user")

    op.create_unique_constraint(
        "uq__user__application_instance_id",
        "user",
        ["application_instance_id", "user_id", "h_userid"],
    )
