"""Migration for auto grading settings."""

import sqlalchemy as sa
from alembic import op

revision = "f521d69a47d2"
down_revision = "ff2f8a64f6a9"


def upgrade() -> None:
    op.create_table(
        "assignment_auto_grading_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "activity_calculation",
            sa.Enum(
                "cumulative",
                "separate",
                name="autogradingcalculation",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column(
            "grading_type",
            sa.Enum(
                "all_or_nothing",
                "scaled",
                name="autogradingtype",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column("required_annotations", sa.Integer(), nullable=False),
        sa.Column("required_replies", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__assignment_auto_grading_config")),
    )
    op.add_column(
        "assignment", sa.Column("auto_grading_config_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk__assignment__auto_grading_config_id__assignment_auto_grading_config"),
        "assignment",
        "assignment_auto_grading_config",
        ["auto_grading_config_id"],
        ["id"],
        ondelete="cascade",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk__assignment__auto_grading_config_id__assignment_auto_grading_config"),
        "assignment",
        type_="foreignkey",
    )
    op.drop_column("assignment", "auto_grading_config_id")
    op.drop_table("assignment_auto_grading_config")
