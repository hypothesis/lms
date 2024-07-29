"""Clean grouping and assignment titles.

Revision ID: e5a9845d55d7
Revises: f8ff7e49cbbf
"""

import sqlalchemy as sa
from alembic import op

revision = "e5a9845d55d7"
down_revision = "f8ff7e49cbbf"


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(
        sa.text(
            """
        UPDATE assignment SET title = TRIM(title)
        WHERE TRIM(title) != title;
    """
        )
    )
    print(f"Assignment titles updated: {result.rowcount}")

    result = conn.execute(
        sa.text(
            """
        UPDATE assignment SET title = null
        WHERE title = '';
    """
        )
    )
    print(f"Empty assignment titles: {result.rowcount}")

    result = conn.execute(
        sa.text(
            """
        UPDATE grouping SET lms_name = TRIM(lms_name)
        WHERE TRIM(lms_name) != lms_name;
    """
        )
    )
    print(f"Grouping titles updated: {result.rowcount}")


def downgrade() -> None:
    pass
