"""Backfill lms_user_application_instance."""

import sqlalchemy as sa
from alembic import op

revision = "e13fb37c96e5"
down_revision = "f61cb94edfc8"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            SELECT
                "user".created,
                "user".updated,
                lms_user.id lms_user_id,
                "user".application_instance_id
            FROM "user"
            JOIN lms_user on lms_user.h_userid = "user".h_userid
        )
        INSERT INTO lms_user_application_instance (
             created,
             updated,
             lms_user_id,
             application_instance_id
        )
        SELECT
           created,
           updated,
           lms_user_id,
           application_instance_id
        FROM backfill
        ON CONFLICT (lms_user_id, application_instance_id) DO NOTHING
    """
        )
    )


def downgrade() -> None:
    pass
