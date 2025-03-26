"""Models to represent users.

These duplicate some of the information stored in User, the main differences being:

    - One LMSUser row per user, not one per (application_instance_id, user) like in User.
    - One or more rows in LMSUserApplicationInstance, one per install we have seen the user in.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base
from lms.models import ApplicationInstance
from lms.models._mixins import CreatedUpdatedMixin


class LMSUser(CreatedUpdatedMixin, Base):
    __tablename__ = "lms_user"

    __table_args__ = (
        # GUID and lti_user_id are unique together.
        # lti_user_id identifies the user within the LMS system and we use GUID to identify each LMS instance
        sa.UniqueConstraint("tool_consumer_instance_guid", "lti_user_id"),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    tool_consumer_instance_guid: Mapped[str | None] = mapped_column(index=True)

    lti_user_id: Mapped[str] = mapped_column(index=True)
    """ID of this user in the LMS, via LTI"""

    lti_v13_user_id: Mapped[str | None] = mapped_column(sa.Unicode)
    """
    The LTI1.3 ID of the user.

    This will be often the same value as lti_user_id but it might be different in:
        - LTI1.1 launches. Where this will be null.
        - Upgraded instances from LTI1.1 where we prefer the LTI1.1 value (if exposed by the LMS).
          In those cases lti_user_id will be the 1.1 value and we'll store here the 1.3 version.
    """

    lms_api_user_id: Mapped[str | None] = mapped_column()
    """
    ID of the user in the proprietary LMS API.
    """

    h_userid: Mapped[str] = mapped_column(unique=True, index=True)
    """The userid value in H. This is calculated hashing tool_consumer_instance_guid and lti_user_id together."""

    email: Mapped[str | None] = mapped_column()

    display_name: Mapped[str | None] = mapped_column(index=True)

    application_instances: Mapped[list[ApplicationInstance]] = relationship(
        secondary="lms_user_application_instance",
        order_by="desc(LMSUserApplicationInstance.updated)",
        viewonly=True,
    )

    @property
    def user_id(self) -> str:
        """Alias lti_user_id to user_if for compatibility with models.User."""
        return self.lti_user_id

    @property
    def application_instance(self):
        return self.application_instances[0]


class LMSUserApplicationInstance(CreatedUpdatedMixin, Base):
    """Record of on which installs (application instances) we have seen one user."""

    __tablename__ = "lms_user_application_instance"

    __table_args__ = (sa.UniqueConstraint("application_instance_id", "lms_user_id"),)

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    application_instance_id: Mapped[int] = mapped_column(
        sa.ForeignKey("application_instances.id", ondelete="cascade"), index=True
    )
    application_instance = relationship("ApplicationInstance")

    lms_user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lms_user.id", ondelete="cascade"), index=True
    )
    lms_user = relationship("LMSUser")
