"""Constrains for grading sync tables."""

import sqlalchemy as sa
from alembic import op

revision = "aea9bbeee574"
down_revision = "f68aacfc62c7"


def upgrade() -> None:
    op.create_index(
        "ix__grading_sync_assignment_status_unique",
        "grading_sync",
        ["assignment_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('scheduled', 'in_progress')"),
    )
    op.create_unique_constraint(
        op.f("uq__grading_sync_grade__grading_sync_id"),
        "grading_sync_grade",
        ["grading_sync_id", "lms_user_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq__grading_sync_grade__grading_sync_id"),
        "grading_sync_grade",
        type_="unique",
    )
    op.drop_index(
        "ix__grading_sync_assignment_status_unique",
        table_name="grading_sync",
        postgresql_where=sa.text("status IN ('scheduled', 'in_progress')"),
    )
