"""Create LMSSegmentRoster."""

import sqlalchemy as sa
from alembic import op

revision = "02d413b4d212"
down_revision = "3466cfe2cbca"


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lms_segment_roster",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lms_segment_id", sa.Integer(), nullable=False),
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
            ["lms_segment_id"],
            ["lms_segment.id"],
            name=op.f("fk__lms_segment_roster__lms_segment_id__lms_segment"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lms_user_id"],
            ["lms_user.id"],
            name=op.f("fk__lms_segment_roster__lms_user_id__lms_user"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["lti_role_id"],
            ["lti_role.id"],
            name=op.f("fk__lms_segment_roster__lti_role_id__lti_role"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__lms_segment_roster")),
        sa.UniqueConstraint(
            "lms_segment_id",
            "lms_user_id",
            "lti_role_id",
            name=op.f("uq__lms_segment_roster__lms_segment_id"),
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("lms_segment_roster")
    # ### end Alembic commands ###