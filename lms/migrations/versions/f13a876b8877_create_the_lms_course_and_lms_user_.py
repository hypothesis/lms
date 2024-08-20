"""Create the lms_course and lms_user tables."""

import sqlalchemy as sa
from alembic import op

revision = "f13a876b8877"
down_revision = "b39108c0cd35"


def upgrade() -> None:
    op.create_table(
        "lms_course",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tool_consumer_instance_guid", sa.String(), nullable=True),
        sa.Column("lti_context_id", sa.String(), nullable=False),
        sa.Column("h_authority_provided_id", sa.String(), nullable=False),
        sa.Column("copied_from_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["copied_from_id"],
            ["lms_course.id"],
            name=op.f("fk__lms_course__copied_from_id__lms_course"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_course")),
        sa.UniqueConstraint(
            "tool_consumer_instance_guid",
            "lti_context_id",
            name=op.f("uq__lms_course__tool_consumer_instance_guid"),
        ),
    )
    op.create_index(
        op.f("ix__lms_course_h_authority_provided_id"),
        "lms_course",
        ["h_authority_provided_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix__lms_course_lti_context_id"),
        "lms_course",
        ["lti_context_id"],
        unique=False,
    )
    op.create_index(op.f("ix__lms_course_name"), "lms_course", ["name"], unique=False)
    op.create_index(
        op.f("ix__lms_course_tool_consumer_instance_guid"),
        "lms_course",
        ["tool_consumer_instance_guid"],
        unique=False,
    )
    op.create_table(
        "lms_user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tool_consumer_instance_guid", sa.String(), nullable=True),
        sa.Column("lti_user_id", sa.String(), nullable=False),
        sa.Column("h_userid", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_user")),
        sa.UniqueConstraint(
            "tool_consumer_instance_guid",
            "lti_user_id",
            name=op.f("uq__lms_user__tool_consumer_instance_guid"),
        ),
    )
    op.create_index(
        op.f("ix__lms_user_display_name"), "lms_user", ["display_name"], unique=False
    )
    op.create_index(
        op.f("ix__lms_user_h_userid"), "lms_user", ["h_userid"], unique=True
    )
    op.create_index(
        op.f("ix__lms_user_lti_user_id"), "lms_user", ["lti_user_id"], unique=False
    )
    op.create_index(
        op.f("ix__lms_user_tool_consumer_instance_guid"),
        "lms_user",
        ["tool_consumer_instance_guid"],
        unique=False,
    )
    op.create_table(
        "lms_course_membership",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lms_course_id", sa.Integer(), nullable=False),
        sa.Column("lms_user_id", sa.Integer(), nullable=False),
        sa.Column("lti_role_id", sa.Integer(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["lms_course_id"],
            ["lms_course.id"],
            name=op.f("fk__lms_course_membership__lms_course_id__lms_course"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lms_user_id"],
            ["lms_course.id"],
            name=op.f("fk__lms_course_membership__lms_user_id__lms_course"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lti_role_id"],
            ["lti_role.id"],
            name=op.f("fk__lms_course_membership__lti_role_id__lti_role"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_course_membership")),
        sa.UniqueConstraint(
            "lms_course_id",
            "lms_user_id",
            "lti_role_id",
            name=op.f("uq__lms_course_membership__lms_course_id"),
        ),
    )
    op.create_index(
        op.f("ix__lms_course_membership_lms_course_id"),
        "lms_course_membership",
        ["lms_course_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__lms_course_membership_lms_user_id"),
        "lms_course_membership",
        ["lms_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__lms_course_membership_lti_role_id"),
        "lms_course_membership",
        ["lti_role_id"],
        unique=False,
    )
    op.create_table(
        "lms_course_application_instance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_instance_id", sa.Integer(), nullable=False),
        sa.Column("lms_course_id", sa.Integer(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["application_instance_id"],
            ["application_instances.id"],
            name=op.f(
                "fk__lms_course_application_instance__application_instance_id__application_instances"
            ),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lms_course_id"],
            ["lms_course.id"],
            name=op.f("fk__lms_course_application_instance__lms_course_id__lms_course"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_course_application_instance")),
        sa.UniqueConstraint(
            "application_instance_id",
            "lms_course_id",
            name=op.f("uq__lms_course_application_instance__application_instance_id"),
        ),
    )
    op.create_index(
        op.f("ix__lms_course_application_instance_application_instance_id"),
        "lms_course_application_instance",
        ["application_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__lms_course_application_instance_lms_course_id"),
        "lms_course_application_instance",
        ["lms_course_id"],
        unique=False,
    )
    op.create_table(
        "lms_user_application_instance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_instance_id", sa.Integer(), nullable=False),
        sa.Column("lms_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["application_instance_id"],
            ["application_instances.id"],
            name=op.f(
                "fk__lms_user_application_instance__application_instance_id__application_instances"
            ),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lms_user_id"],
            ["lms_user.id"],
            name=op.f("fk__lms_user_application_instance__lms_user_id__lms_user"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_user_application_instance")),
        sa.UniqueConstraint(
            "application_instance_id",
            "lms_user_id",
            name=op.f("uq__lms_user_application_instance__application_instance_id"),
        ),
    )
    op.create_index(
        op.f("ix__lms_user_application_instance_application_instance_id"),
        "lms_user_application_instance",
        ["application_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__lms_user_application_instance_lms_user_id"),
        "lms_user_application_instance",
        ["lms_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix__lms_user_application_instance_lms_user_id"),
        table_name="lms_user_application_instance",
    )
    op.drop_index(
        op.f("ix__lms_user_application_instance_application_instance_id"),
        table_name="lms_user_application_instance",
    )
    op.drop_table("lms_user_application_instance")
    op.drop_index(
        op.f("ix__lms_course_application_instance_lms_course_id"),
        table_name="lms_course_application_instance",
    )
    op.drop_index(
        op.f("ix__lms_course_application_instance_application_instance_id"),
        table_name="lms_course_application_instance",
    )
    op.drop_table("lms_course_application_instance")
    op.drop_index(
        op.f("ix__lms_course_membership_lti_role_id"),
        table_name="lms_course_membership",
    )
    op.drop_index(
        op.f("ix__lms_course_membership_lms_user_id"),
        table_name="lms_course_membership",
    )
    op.drop_index(
        op.f("ix__lms_course_membership_lms_course_id"),
        table_name="lms_course_membership",
    )
    op.drop_table("lms_course_membership")
    op.drop_index(
        op.f("ix__lms_user_tool_consumer_instance_guid"), table_name="lms_user"
    )
    op.drop_index(op.f("ix__lms_user_lti_user_id"), table_name="lms_user")
    op.drop_index(op.f("ix__lms_user_h_userid"), table_name="lms_user")
    op.drop_index(op.f("ix__lms_user_display_name"), table_name="lms_user")
    op.drop_table("lms_user")
    op.drop_index(
        op.f("ix__lms_course_tool_consumer_instance_guid"), table_name="lms_course"
    )
    op.drop_index(op.f("ix__lms_course_name"), table_name="lms_course")
    op.drop_index(op.f("ix__lms_course_lti_context_id"), table_name="lms_course")
    op.drop_index(
        op.f("ix__lms_course_h_authority_provided_id"), table_name="lms_course"
    )
    op.drop_table("lms_course")
