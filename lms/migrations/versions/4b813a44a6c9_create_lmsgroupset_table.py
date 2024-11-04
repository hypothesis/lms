"""Create LMSGroupSet table."""

import sqlalchemy as sa
from alembic import op

revision = "4b813a44a6c9"
down_revision = "a9e5a33e96b7"


def upgrade() -> None:
    op.create_table(
        "lms_group_set",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lms_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("lms_course_id", sa.Integer(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["lms_course_id"],
            ["lms_course.id"],
            name=op.f("fk__lms_group_set__lms_course_id__lms_course"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_group_set")),
        sa.UniqueConstraint(
            "lms_course_id", "lms_id", name=op.f("uq__lms_group_set__lms_course_id")
        ),
    )
    op.create_index(
        op.f("ix__lms_group_set_lms_id"), "lms_group_set", ["lms_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_index(op.f("ix__lms_group_set_lms_id"), table_name="lms_group_set")
    op.drop_table("lms_group_set")
