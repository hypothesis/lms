"""
Add ApplicationInstance.consumer_key unique constraint.

Revision ID: cfd94b1300ce
Revises: 83f18f61c76a
Create Date: 2019-03-07 15:43:56.641856

"""
from alembic import op


revision = "cfd94b1300ce"
down_revision = "83f18f61c76a"


def upgrade():
    op.create_unique_constraint(
        "uq__application_instances__consumer_key",
        "application_instances",
        ["consumer_key"],
    )


def downgrade():
    op.drop_constraint(
        "uq__application_instances__consumer_key", "application_instances"
    )
