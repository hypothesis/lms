"""Create the lms_term table."""

import sqlalchemy as sa
from alembic import op

revision = "a8fd48c30957"
down_revision = "9be518500f7d"


def upgrade() -> None:
    op.create_table(
        "lms_term",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tool_consumer_instance_guid", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("lms_id", sa.String(), nullable=True),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_term")),
    )
    op.create_index(op.f("ix__lms_term_key"), "lms_term", ["key"], unique=True)
    op.create_index(op.f("ix__lms_term_lms_id"), "lms_term", ["lms_id"], unique=False)
    op.create_index(
        op.f("ix__lms_term_tool_consumer_instance_guid"),
        "lms_term",
        ["tool_consumer_instance_guid"],
        unique=False,
    )
    op.add_column("lms_course", sa.Column("lms_term_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix__lms_course_lms_term_id"), "lms_course", ["lms_term_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk__lms_course__lms_term_id__lms_term"),
        "lms_course",
        "lms_term",
        ["lms_term_id"],
        ["id"],
        ondelete="cascade",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk__lms_course__lms_term_id__lms_term"), "lms_course", type_="foreignkey"
    )
    op.drop_index(op.f("ix__lms_course_lms_term_id"), table_name="lms_course")
    op.drop_column("lms_course", "lms_term_id")
    op.drop_index(
        op.f("ix__lms_term_tool_consumer_instance_guid"), table_name="lms_term"
    )
    op.drop_index(op.f("ix__lms_term_lms_id"), table_name="lms_term")
    op.drop_index(op.f("ix__lms_term_key"), table_name="lms_term")
    op.drop_table("lms_term")
