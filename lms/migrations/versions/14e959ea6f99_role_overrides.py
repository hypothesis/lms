"""Create the role_overrides table.

Revision ID: 14e959ea6f99
Revises: 0c52a13c6cad
"""

import sqlalchemy as sa
from alembic import op

revision = "14e959ea6f99"
down_revision = "0c52a13c6cad"


def upgrade() -> None:
    op.create_table(
        "lti_role_override",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lti_role_id", sa.Integer(), nullable=True),
        sa.Column("application_instance_id", sa.Integer(), nullable=False),
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
        sa.Column(
            "scope",
            sa.Enum(
                "course",
                "institution",
                "system",
                name="rolescope",
                native_enum=False,
                length=64,
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["application_instance_id"],
            ["application_instances.id"],
            name=op.f(
                "fk__lti_role_override__application_instance_id__application_instances"
            ),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lti_role_id"],
            ["lti_role.id"],
            name=op.f("fk__lti_role_override__lti_role_id__lti_role"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lti_role_override")),
        sa.UniqueConstraint(
            "application_instance_id",
            "lti_role_id",
            name=op.f("uq__lti_role_override__application_instance_id"),
        ),
    )
    op.create_index(
        op.f("ix__lti_role_override_lti_role_id"),
        "lti_role_override",
        ["lti_role_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix__lti_role_override_lti_role_id"), table_name="lti_role_override"
    )
    op.drop_table("lti_role_override")
