"""
Add updated and last_launched to application instances.

Revision ID: 64fd59a9f4b6
Revises: 53f9ad3b93a4
Create Date: 2023-02-02 16:56:37.882370

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "64fd59a9f4b6"
down_revision = "53f9ad3b93a4"


def upgrade():
    op.add_column(
        "application_instances",
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
    )

    op.add_column(
        "application_instances",
        sa.Column("last_launched", sa.DateTime(), nullable=True),
    )

    # Default the last launched date to the most recent deep linking or launch
    op.execute(
        """
        WITH
            last_update_times AS (
                SELECT
                    application_instance_id,
                    MAX(timestamp) AS last_launched
                FROM event
                JOIN event_type ON
                    event_type.id = event.type_id
                WHERE
                    event_type.type IN ('deep_linking', 'configured_launch')
                    AND application_instance_id IS NOT NULL
                GROUP BY application_instance_id
            )

        UPDATE application_instances
        SET last_launched=last_update_times.last_launched
        FROM last_update_times
        WHERE id = last_update_times.application_instance_id
    """
    )

    # Default the updated date to the existing created date / launched date
    op.execute(
        "UPDATE application_instances SET updated=COALESCE(last_launched, created)"
    )


def downgrade():
    op.drop_column("application_instances", "last_launched")
    op.drop_column("application_instances", "updated")
