"""LMSCourseApplicationInstance backfill

Revision ID: 9e79650bed37
Revises: f61cb94edfc8
"""
from alembic import op
import sqlalchemy as sa


revision = "9e79650bed37"
down_revision = "f61cb94edfc8"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        WITH backfill as (
            select "grouping".created, "grouping".updated, lms_course.id lms_course_id, "grouping".application_instance_id 
            from "grouping" 
            join lms_course on lms_course.authority_provided_id = "grouping".authority_provided_id
        )
        INSERT INTO lms_course_application_instance (
             created,
             updated,
             lms_course_id,
             application_instance_id
        )
        SELECT
           created,
           updated,
           lms_course_id,
           application_instance_id
        FROM backfill
        ON CONFLICT (lms_course_id, application_instance_id) DO NOTHING
    """
        )
    )


def downgrade() -> None:
    pass
