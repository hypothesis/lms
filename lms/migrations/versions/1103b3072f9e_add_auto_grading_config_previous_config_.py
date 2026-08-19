"""Add assignment_auto_grading_config.previous_config_id.

Revision ID: 1103b3072f9e
Revises: fa62e42cb531
"""

import sqlalchemy as sa
from alembic import op

revision = "1103b3072f9e"
down_revision = "fa62e42cb531"

# The generated name (fk__<table>__<column>__<table>) is too long, over
# Postgres's limit, so we name it explicitly instead.
FK_NAME = "fk__aagc__previous_config_id__aagc"
UQ_NAME = "uq__assignment_auto_grading_config__previous_config_id"


def upgrade() -> None:
    op.add_column(
        "assignment_auto_grading_config",
        sa.Column("previous_config_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        FK_NAME,
        "assignment_auto_grading_config",
        "assignment_auto_grading_config",
        ["previous_config_id"],
        ["id"],
        ondelete="cascade",
    )
    # Each config can be the predecessor of at most one other, which rules out
    # forks. NULLS DISTINCT (the default) is required, not incidental: every
    # assignment's first config has previous_config_id NULL.
    op.create_unique_constraint(
        UQ_NAME, "assignment_auto_grading_config", ["previous_config_id"]
    )


def downgrade() -> None:
    op.drop_constraint(UQ_NAME, "assignment_auto_grading_config", type_="unique")
    op.drop_constraint(FK_NAME, "assignment_auto_grading_config", type_="foreignkey")
    op.drop_column("assignment_auto_grading_config", "previous_config_id")
