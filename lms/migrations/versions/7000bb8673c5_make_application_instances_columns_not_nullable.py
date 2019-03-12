"""
Make application_instances columns not nullable.

Add NOT NULL constraints to various application_instances columns that should
have them.

Revision ID: 7000bb8673c5
Revises: cfd94b1300ce
Create Date: 2019-03-11 15:37:18.071294

"""
from alembic import op


revision = "7000bb8673c5"
down_revision = "cfd94b1300ce"


def upgrade():
    op.alter_column("application_instances", "consumer_key", nullable=False)
    op.alter_column("application_instances", "shared_secret", nullable=False)
    op.alter_column("application_instances", "lms_url", nullable=False)
    op.alter_column("application_instances", "requesters_email", nullable=False)
    op.alter_column("application_instances", "created", nullable=False)


def downgrade():
    op.alter_column("application_instances", "consumer_key", nullable=True)
    op.alter_column("application_instances", "shared_secret", nullable=True)
    op.alter_column("application_instances", "lms_url", nullable=True)
    op.alter_column("application_instances", "requesters_email", nullable=True)
    op.alter_column("application_instances", "created", nullable=True)
