"""AI.tool_consumer_instance_guid index.

Revision ID: 1337584e2b07
Revises: 8e203ad93a58
"""

import sqlalchemy as sa
from alembic import op

revision = "1337584e2b07"
down_revision = "8e203ad93a58"


def upgrade() -> None:
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")

    op.create_index(
        op.f("ix__application_instances_tool_consumer_instance_guid"),
        "application_instances",
        ["tool_consumer_instance_guid"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix__application_instances_tool_consumer_instance_guid"),
        table_name="application_instances",
    )
