import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class User(CreatedUpdatedMixin, Base):
    """A user record to link between LTI users and H users."""

    __tablename__ = "user"
    __table_args__ = (
        sa.UniqueConstraint(
            "application_instance_id",
            "user_id",
            name="uq__user__application_instance_id__user_id",
        ),
        sa.UniqueConstraint(
            "application_instance_id",
            "h_userid",
            name="uq__user__application_instance_id__h_userid",
        ),
        sa.Index("ix__user_h_user_updated", "h_userid", sa.desc("updated")),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    """An arbitrary primary id."""

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )
    application_instance = sa.orm.relationship("ApplicationInstance")

    user_id: Mapped[str] = mapped_column(sa.Unicode, nullable=False)
    """The user id provided by the LTI parameters."""

    roles = sa.Column(sa.Unicode, nullable=True)
    """The roles provided by the LTI parameters."""

    h_userid: Mapped[str] = mapped_column(sa.Unicode, index=True)
    """The H userid which is created from LTI provided values."""

    email: Mapped[str | None] = mapped_column(sa.Unicode)
    """Email address of the user"""

    display_name: Mapped[str | None] = mapped_column(sa.Unicode, index=True)
    """The user's display name."""


class LMSUser(CreatedUpdatedMixin, Base):
    """A user record for each LMS user."""

    __tablename__ = "lms_user"
    __table_args__ = (sa.UniqueConstraint("tool_consumer_instance_guid", "lti_id"),)

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    tool_consumer_instance_guid: Mapped[str | None] = mapped_column(
        sa.UnicodeText, index=True
    )

    h_userid: Mapped[str] = mapped_column(sa.Unicode, unique=True, index=True)
    """The H userid which is created from LTI provided values."""

    lti_id: Mapped[str] = mapped_column(sa.Unicode, index=True)
    """ID of this user in the LMS, via LTI"""

    email: Mapped[str | None] = mapped_column(sa.Unicode)
    """Email address of the user"""

    name: Mapped[str | None] = mapped_column(sa.Unicode, index=True)
    """The user's display name."""


class LMSUserApplicationInstance(CreatedUpdatedMixin, Base):
    __tablename__ = "lms_user_application_instance"

    __table_args__ = (sa.UniqueConstraint("application_instance_id", "lms_user_id"),)

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    application_instance_id: Mapped[int] = sa.Column(
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
    )

    lms_user_id: Mapped[int] = sa.Column(
        sa.ForeignKey("lms_user.id", ondelete="cascade"),
    )
