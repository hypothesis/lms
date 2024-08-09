"""Add missing indexes for FKs."""

import sqlalchemy as sa
from alembic import op

revision = "3d0c022c716c"
down_revision = "7858a12c4e4a"


def upgrade() -> None:
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")

    op.create_index(
        op.f("ix__assignment_grouping_assignment_id"),
        "assignment_grouping",
        ["assignment_id"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__assignment_grouping_grouping_id"),
        "assignment_grouping",
        ["grouping_id"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__assignment_membership_assignment_id"),
        "assignment_membership",
        ["assignment_id"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__grouping_membership_user_id"),
        "grouping_membership",
        ["user_id"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__assignment_course_id"),
        "assignment",
        ["course_id"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    op.execute("COMMIT")

    op.drop_index(
        op.f("ix__grouping_membership_user_id"),
        table_name="grouping_membership",
        postgresql_concurrently=True,
    )
    op.drop_index(
        op.f("ix__assignment_membership_assignment_id"),
        table_name="assignment_membership",
        postgresql_concurrently=True,
    )
    op.drop_index(
        op.f("ix__assignment_grouping_grouping_id"),
        table_name="assignment_grouping",
        postgresql_concurrently=True,
    )
    op.drop_index(
        op.f("ix__assignment_grouping_assignment_id"),
        table_name="assignment_grouping",
        postgresql_concurrently=True,
    )
    op.drop_index(
        op.f("ix__assignment_course_id"),
        table_name="assignment",
        postgresql_concurrently=True,
    )
