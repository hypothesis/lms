"""Add missing indexes for dashboard queries."""

import sqlalchemy as sa
from alembic import op

revision = "ca27e52b7303"
down_revision = "e5a9845d55d7"


def upgrade() -> None:
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")

    op.create_index(
        op.f("ix__assignment_membership_lti_role_id"),
        "assignment_membership",
        ["lti_role_id"],
        unique=False,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("ix__user_h_userid"),
        "user",
        ["h_userid"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix__user_h_userid"), table_name="user")
    op.drop_index(
        op.f("ix__assignment_membership_lti_role_id"),
        table_name="assignment_membership",
    )
