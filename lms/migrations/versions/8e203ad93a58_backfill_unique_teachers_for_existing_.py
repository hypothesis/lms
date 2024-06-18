"""Backfill unique teachers for existing reports.

Revision ID: 8e203ad93a58
Revises: da01fe01c324
"""

import sqlalchemy as sa
from alembic import op

revision = "8e203ad93a58"
down_revision = "da01fe01c324"


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            """
        WITH teacher_counts as (
            SELECT
                organization_usage_report.id,
                count(distinct h_userid ) FILTER(WHERE email <> '<STUDENT>') unique_teachers
            FROM
                organization_usage_report,
                jsonb_array_elements(report) AS report_row,
                jsonb_to_record(report_row) AS usage_user(email text, h_userid text)
            GROUP BY organization_usage_report.id
        )
            UPDATE organization_usage_report SET unique_teachers = teacher_counts.unique_teachers from teacher_counts where teacher_counts.id = organization_usage_report.id;
        """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE organization_usage_report SET unique_teachers = null;")
    )
