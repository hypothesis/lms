"""Add indexes for names we sort by in the dashboards."""

import sqlalchemy as sa
from alembic import op

revision = "afa53b7464be"
down_revision = "ca27e52b7303"


def upgrade() -> None:
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")

    op.create_index(
        op.f("ix__assignment_title"),
        "assignment",
        ["title"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__grouping_lms_name"),
        "grouping",
        ["lms_name"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__user_display_name"),
        "user",
        ["display_name"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix__user_display_name"), table_name="user")
    op.drop_index(op.f("ix__grouping_lms_name"), table_name="grouping")
    op.drop_index(op.f("ix__assignment_title"), table_name="assignment")
