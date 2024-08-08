"""Add index for user deduplication."""

import sqlalchemy as sa
from alembic import op

revision = "7858a12c4e4a"
down_revision = "f6c442c861c4"


def upgrade() -> None:
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")

    op.create_index(
        "ix__user_h_user__updated",
        "user",
        ["h_userid", sa.text("updated DESC")],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    op.drop_index("id__h_user_updated_for_deduplication", table_name="user")
