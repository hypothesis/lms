"""
Add course FK to assignment.

Revision ID: db6c3498b77f
Revises: 2119e1c621de
Create Date: 2022-03-28 13:19:03.407218

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "db6c3498b77f"
down_revision = "2119e1c621de"


def upgrade():
    op.add_column(
        "module_item_configurations",
        sa.Column("course_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk__module_item_configurations__course_id__grouping"),
        "module_item_configurations",
        "grouping",
        ["course_id"],
        ["id"],
        ondelete="cascade",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__module_item_configurations__course_id__grouping"),
        "module_item_configurations",
        type_="foreignkey",
    )
    op.drop_column("module_item_configurations", "course_id")
