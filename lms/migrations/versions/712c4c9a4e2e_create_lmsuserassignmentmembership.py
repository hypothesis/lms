"""Create LMSUserAssignmentMembership."""

import sqlalchemy as sa
from alembic import op

revision = "712c4c9a4e2e"
down_revision = "aea9bbeee574"


def upgrade() -> None:
    op.create_table(
        "lms_user_assignment_membership",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("lms_user_id", sa.Integer(), nullable=False),
        sa.Column("lti_role_id", sa.Integer(), nullable=False),
        sa.Column("lti_v11_lis_result_sourcedid", sa.String(), nullable=True),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk__lms_user_assignment_membership__assignment_id__assignment"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lms_user_id"],
            ["lms_user.id"],
            name=op.f("fk__lms_user_assignment_membership__lms_user_id__lms_user"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lti_role_id"],
            ["lti_role.id"],
            name=op.f("fk__lms_user_assignment_membership__lti_role_id__lti_role"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_user_assignment_membership")),
        sa.UniqueConstraint(
            "assignment_id",
            "lms_user_id",
            "lti_role_id",
            name=op.f("uq__lms_user_assignment_membership__assignment_id"),
        ),
    )
    op.create_index(
        op.f("ix__lms_user_assignment_membership_assignment_id"),
        "lms_user_assignment_membership",
        ["assignment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__lms_user_assignment_membership_lms_user_id"),
        "lms_user_assignment_membership",
        ["lms_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__lms_user_assignment_membership_lti_role_id"),
        "lms_user_assignment_membership",
        ["lti_role_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix__lms_user_assignment_membership_lti_role_id"),
        table_name="lms_user_assignment_membership",
    )
    op.drop_index(
        op.f("ix__lms_user_assignment_membership_lms_user_id"),
        table_name="lms_user_assignment_membership",
    )
    op.drop_index(
        op.f("ix__lms_user_assignment_membership_assignment_id"),
        table_name="lms_user_assignment_membership",
    )
    op.drop_table("lms_user_assignment_membership")
