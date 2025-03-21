"""Create the notification table."""

import sqlalchemy as sa
from alembic import op

revision = "0d265909ff85"
down_revision = "a8fd48c30957"


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "notification_type",
            sa.Enum("reply", name="type", native_enum=False, length=64),
            nullable=False,
        ),
        sa.Column("source_annotation_id", sa.String(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk__notification__assignment_id__assignment"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["lms_user.id"],
            name=op.f("fk__notification__recipient_id__lms_user"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["lms_user.id"],
            name=op.f("fk__notification__sender_id__lms_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__notification")),
        sa.UniqueConstraint(
            "recipient_id",
            "source_annotation_id",
            name="uq__notification__recipient_id__source_annotation_id",
        ),
    )
    op.create_index(
        op.f("ix__notification_recipient_id"),
        "notification",
        ["recipient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__notification_sender_id"), "notification", ["sender_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix__notification_sender_id"), table_name="notification")
    op.drop_index(op.f("ix__notification_recipient_id"), table_name="notification")
    op.drop_table("notification")
