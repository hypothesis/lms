"""backfill lms_user_application_instance

Revision ID: e13fb37c96e5
Revises: aef6a6460d0d
"""
from alembic import op
import sqlalchemy as sa


revision = "e13fb37c96e5"
down_revision = "aef6a6460d0d"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            select "user".created, "user".updated, lms_user.id lms_user_id, "user".application_instance_id 
            from "user" 
            join lms_user on lms_user.h_userid = "user".h_userid
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
