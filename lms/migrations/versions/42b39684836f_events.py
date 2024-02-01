"""
Add events, event_type, event_user and event_data tables.

Revision ID: 42b39684836f
Revises: 1e146996cca6
Create Date: 2022-07-29 16:25:30.907904

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "42b39684836f"
down_revision = "1e146996cca6"


def upgrade():
    op.create_table(
        "event_type",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "configured_launch",
                "deep_linking",
                name="type",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__event_type")),
    )
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("type_id", sa.Integer(), nullable=True),
        sa.Column("application_instance_id", sa.Integer(), nullable=True),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        sa.Column("grouping_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_instance_id"],
            ["application_instances.id"],
            name=op.f("fk__event__application_instance_id__application_instances"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk__event__assignment_id__assignment"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["grouping.id"],
            name=op.f("fk__event__course_id__grouping"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["grouping_id"],
            ["grouping.id"],
            name=op.f("fk__event__grouping_id__grouping"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["event_type.id"],
            name=op.f("fk__event__type_id__event_type"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__event")),
    )
    op.create_index(op.f("ix__event_timestamp"), "event", ["timestamp"], unique=False)
    op.create_index(
        op.f("ix__event_application_instance_id"),
        "event",
        ["application_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__event_assignment_id"), "event", ["assignment_id"], unique=False
    )
    op.create_index(op.f("ix__event_course_id"), "event", ["course_id"], unique=False)
    op.create_index(op.f("ix__event_type_id"), "event", ["type_id"], unique=False)
    op.create_table(
        "event_data",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column(
            "extra",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
            name=op.f("fk__event_data__event_id__event"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("event_id", name=op.f("pk__event_data")),
    )
    op.create_table(
        "event_user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lti_role_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
            name=op.f("fk__event_user__event_id__event"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lti_role_id"],
            ["lti_role.id"],
            name=op.f("fk__event_user__lti_role_id__lti_role"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__event_user__user_id__user"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", "event_id", name=op.f("pk__event_user")),
        sa.UniqueConstraint(
            "event_id", "user_id", "lti_role_id", name=op.f("uq__event_user__event_id")
        ),
    )
    op.create_index(
        op.f("ix__event_user_lti_role_id"), "event_user", ["lti_role_id"], unique=False
    )
    op.create_index(
        op.f("ix__event_user_user_id"), "event_user", ["user_id"], unique=False
    )

    # Manually insert the event_types
    conn = op.get_bind()
    conn.execute("""INSERT INTO event_type (type) values ('configured_launch')""")
    conn.execute("""INSERT INTO event_type (type) values ('deep_linking')""")


def downgrade():
    op.drop_table("event_user")
    op.drop_table("event_data")
    op.drop_index(op.f("ix__event_timestamp"), table_name="event")
    op.drop_table("event")
    op.drop_table("event_type")
