"""Assignment Rosters table."""

import sqlalchemy as sa
from alembic import op

revision = "cb5fe6e8dc09"
down_revision = "481968561169"


def upgrade() -> None:
    op.create_table(
        "assignment_roster",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("lms_user_id", sa.Integer(), nullable=False),
        sa.Column("lti_role_id", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk__assignment_roster__assignment_id__assignment"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lms_user_id"],
            ["lms_user.id"],
            name=op.f("fk__assignment_roster__lms_user_id__lms_user"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lti_role_id"],
            ["lti_role.id"],
            name=op.f("fk__assignment_roster__lti_role_id__lti_role"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__assignment_roster")),
        sa.UniqueConstraint(
            "assignment_id",
            "lms_user_id",
            "lti_role_id",
            name=op.f("uq__assignment_roster__assignment_id"),
        ),
    )


def downgrade() -> None:
    op.drop_table("assignment_roster")
