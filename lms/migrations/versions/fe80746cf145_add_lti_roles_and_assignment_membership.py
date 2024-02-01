"""
Add lti_roles and assignment_membership.

Revision ID: fe80746cf145
Revises: 83ec5ef85d44
Create Date: 2022-06-08 20:37:02.158624

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fe80746cf145"
down_revision = "83ec5ef85d44"


def upgrade():
    op.create_table(
        "lti_role",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("value", sa.UnicodeText(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "instructor",
                "learner",
                "admin",
                name="roletype",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lti_role")),
        sa.UniqueConstraint("value", name=op.f("uq__lti_role__value")),
    )

    op.create_table(
        "assignment_membership",
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lti_role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk__assignment_membership__assignment_id__assignment"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lti_role_id"],
            ["lti_role.id"],
            name=op.f("fk__assignment_membership__lti_role_id__lti_role"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__assignment_membership__user_id__user"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint(
            "assignment_id",
            "user_id",
            "lti_role_id",
            name=op.f("pk__assignment_membership"),
        ),
    )


def downgrade():
    op.drop_table("assignment_membership")
    op.drop_table("lti_role")
