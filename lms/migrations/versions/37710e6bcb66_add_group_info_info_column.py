"""
Add group_info.info column.

Revision ID: 37710e6bcb66
Revises: a930adadac74
Create Date: 2020-04-30 12:21:20.645402

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

# revision identifiers, used by Alembic.
revision = "37710e6bcb66"
down_revision = "a930adadac74"


def upgrade():
    op.add_column(
        "group_info", sa.Column("info", MutableDict.as_mutable(JSONB)),
    )
    group_info_table = sa.table(
        "group_info", sa.Column("info", MutableDict.as_mutable(JSONB))
    )
    op.execute(group_info_table.update().values(info={"instructors": []}))


def downgrade():
    op.drop_column("group_info", "info")
