"""Migration for grading_sync tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f68aacfc62c7"
down_revision = "adc83819c8d8"


def upgrade() -> None:
    op.create_table(
        "grading_sync",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "in_progress",
                "finished",
                "failed",
                name="autogradingsyncstatus",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk__grading_sync__assignment_id__assignment"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["lms_user.id"],
            name=op.f("fk__grading_sync__created_by_id__lms_user"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__grading_sync")),
    )
    op.create_index(
        op.f("ix__grading_sync_assignment_id"),
        "grading_sync",
        ["assignment_id"],
        unique=False,
    )

    op.create_table(
        "grading_sync_grade",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("grading_sync_id", sa.Integer(), nullable=False),
        sa.Column("lms_user_id", sa.Integer(), nullable=False),
        sa.Column("grade", sa.Float(), nullable=False),
        sa.Column(
            "error_details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["grading_sync_id"],
            ["grading_sync.id"],
            name=op.f("fk__grading_sync_grade__grading_sync_id__grading_sync"),
        ),
        sa.ForeignKeyConstraint(
            ["lms_user_id"],
            ["lms_user.id"],
            name=op.f("fk__grading_sync_grade__lms_user_id__lms_user"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__grading_sync_grade")),
    )
    op.create_index(
        op.f("ix__grading_sync_grade_grading_sync_id"),
        "grading_sync_grade",
        ["grading_sync_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__grading_sync_grade_lms_user_id"),
        "grading_sync_grade",
        ["lms_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix__grading_sync_grade_lms_user_id"), table_name="grading_sync_grade"
    )
    op.drop_index(
        op.f("ix__grading_sync_grade_grading_sync_id"), table_name="grading_sync_grade"
    )
    op.drop_table("grading_sync_grade")
    op.drop_index(op.f("ix__grading_sync_assignment_id"), table_name="grading_sync")
    op.drop_table("grading_sync")
