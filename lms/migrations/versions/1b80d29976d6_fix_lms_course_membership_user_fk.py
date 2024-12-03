"""Fix lms_course_membership user FK."""

from alembic import op

revision = "1b80d29976d6"
down_revision = "f13a876b8877"


def upgrade() -> None:
    op.drop_constraint(
        "fk__lms_course_membership__lms_user_id__lms_course",
        "lms_course_membership",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk__lms_course_membership__lms_user_id__lms_user"),
        "lms_course_membership",
        "lms_user",
        ["lms_user_id"],
        ["id"],
        ondelete="cascade",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk__lms_course_membership__lms_user_id__lms_user"),
        "lms_course_membership",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk__lms_course_membership__lms_user_id__lms_course",
        "lms_course_membership",
        "lms_course",
        ["lms_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
