"""Add Assignment.lms_course_id."""

from alembic import op
import sqlalchemy as sa


revision = "81c7b13978ea"
down_revision = "16ad8b08e0dd"


def upgrade() -> None:
    op.add_column("assignment", sa.Column("lms_course_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix__assignment_lms_course_id"),
        "assignment",
        ["lms_course_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk__assignment__lms_course_id__lms_course"),
        "assignment",
        "lms_course",
        ["lms_course_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk__assignment__lms_course_id__lms_course"),
        "assignment",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix__assignment_lms_course_id"), table_name="assignment")
    op.drop_column("assignment", "lms_course_id")
