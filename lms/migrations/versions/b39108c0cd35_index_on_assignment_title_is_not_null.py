"""Index on assignment.title is not null."""

import sqlalchemy as sa
from alembic import op

revision = "b39108c0cd35"
down_revision = "3d0c022c716c"


def upgrade() -> None:
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")

    op.create_index(
        "ix__assignment_title_is_not_null",
        "assignment",
        ["title"],
        unique=False,
        postgresql_where=sa.text("title IS NOT NULL"),
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    op.execute("COMMIT")

    op.drop_index(
        "ix__assignment_title_is_not_null",
        table_name="assignment",
        postgresql_where=sa.text("title IS NOT NULL"),
        postgresql_concurrently=True,
    )
