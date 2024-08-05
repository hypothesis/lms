"""Backfill assignment.course_id."""

import sqlalchemy as sa
from alembic import op

revision = "f6c442c861c4"
down_revision = "18109b584a5b"


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            """
        WITH assignment_courses as (
          SELECT DISTINCT ON (assignment.id) assignment.id as assignment_id, grouping.id  as course_id
          FROM assignment
          JOIN assignment_grouping on assignment.id = assignment_grouping.assignment_id
          JOIN grouping on grouping.id = grouping_id
          -- Only courses, not sections or groups
          WHERE grouping.type = 'course'
          -- Don't override data we already set since we created the column
          and assignment.course_id is null
          -- Order for the `DISTINCT ON`, when duplicate found for one assignment, pick the latest
          ORDER BY assignment.id, assignment_grouping.created desc
       )
          UPDATE assignment set course_id = assignment_courses.course_id
          FROM assignment_courses
          WHERE assignment.id = assignment_courses.assignment_id
    """
        )
    )


def downgrade() -> None:
    pass
