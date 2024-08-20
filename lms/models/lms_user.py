"""Models to represent users.

These duplicate some of the information stored in User, the main differences being:

    - One LMSUser row per user, not one per (application_instance_id, user) like in User.
    - One or more rows in LMSUserApplicationInstance, one per install we have seen the user in.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class LMSUser(CreatedUpdatedMixin, Base):
    __tablename__ = "lms_user"

    __table_args__ = (
        # GUID and lti_user_id are unique together.
        # lti_user_id identifies the user within the LMS system and we use GUID to identify each LMS instance
        sa.UniqueConstraint("tool_consumer_instance_guid", "lti_user_id"),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    tool_consumer_instance_guid: Mapped[str | None] = mapped_column(
        sa.UnicodeText, index=True
    )

    lti_user_id: Mapped[str] = mapped_column(sa.Unicode, index=True)
    """ID of this user in the LMS, via LTI"""

    h_userid: Mapped[str] = mapped_column(sa.Unicode, unique=True, index=True)
    """The userid value in H. This is calculated hashing tool_consumer_instance_guid and lti_user_id together."""

    email: Mapped[str | None] = mapped_column(sa.Unicode)

    display_name: Mapped[str | None] = mapped_column(sa.Unicode, index=True)


class LMSUserApplicationInstance(CreatedUpdatedMixin, Base):
    """Record of on which installs (application instances) we have seen one user."""

    __tablename__ = "lms_user_application_instance"

    __table_args__ = (sa.UniqueConstraint("application_instance_id", "lms_user_id"),)

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    application_instance_id: Mapped[int] = mapped_column(
        sa.ForeignKey("application_instances.id", ondelete="cascade"), index=True
    )

    lms_user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lms_user.id", ondelete="cascade"), index=True
    )
