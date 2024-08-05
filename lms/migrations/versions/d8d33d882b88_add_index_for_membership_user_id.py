"""Add index for membership.user_id."""

import sqlalchemy as sa
from alembic import op

revision = "d8d33d882b88"
down_revision = "afa53b7464be"


def upgrade() -> None:
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")

    op.create_index(
        op.f("ix__assignment_membership_user_id"),
        "assignment_membership",
        ["user_id"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix__assignment_membership_user_id"), table_name="assignment_membership"
    )
