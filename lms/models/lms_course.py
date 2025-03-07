"""Models to represent courses.

These duplicate some of the information stored in Grouping and GroupingMembership, the main differences being:

    - One LMSCourse row per course, not one per (application_instance_id, course) like in Grouping.
    - One or more rows in LMSCourseApplicationInstance, one per install we have seen the course in.
    - LMSCourse membership stores role information, GroupingMembership doesn't.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base
from lms.models import ApplicationInstance
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.family import Family

if TYPE_CHECKING:
    from lms.models import LMSTerm, LMSUser, LTIRole


class LMSCourse(CreatedUpdatedMixin, Base):
    __tablename__ = "lms_course"
    __table_args__ = (
        # GUID and lti_context_id are unique together.
        # lti_context_id identifies the course within the LMS system and we use GUID to identify each LMS instance
        sa.UniqueConstraint("tool_consumer_instance_guid", "lti_context_id"),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    tool_consumer_instance_guid: Mapped[str | None] = mapped_column(index=True)

    lti_context_id: Mapped[str] = mapped_column(index=True)
    """ID of this course in the LMS, via LTI. "Context"" is using the LTI nomenclature."""

    lms_api_course_id: Mapped[str | None] = mapped_column()
    """
    ID of the course in the propietary LMS API.
    """

    h_authority_provided_id: Mapped[str] = mapped_column(unique=True, index=True)
    """The Group.authority_provided_id value in H. This is calculated hashing tool_consumer_instance_guid and lti_context_id together."""

    copied_from_id: Mapped[int | None] = mapped_column(sa.ForeignKey("lms_course.id"))
    """ID of the course grouping this one was copied from using the course copy feature in the LMS."""

    name: Mapped[str] = mapped_column(index=True)

    lti_context_memberships_url: Mapped[str | None] = mapped_column()
    """URL for the Names and Roles endpoint, stored during launch to use it outside the launch context."""

    starts_at: Mapped[datetime | None] = mapped_column()
    """The start date of the course. Only for when we get this information directly from the LMS"""

    ends_at: Mapped[datetime | None] = mapped_column()
    """The end date of the course. Only for when we get this information directly from the LMS"""

    lms_term_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("lms_term.id", ondelete="cascade"), index=True
    )
    lms_term: Mapped["LMSTerm"] = relationship()

    application_instances: Mapped[list[ApplicationInstance]] = relationship(
        secondary="lms_course_application_instance",
        order_by="desc(LMSCourseApplicationInstance.updated)",
        viewonly=True,
    )

    @property
    def lms_url(self) -> str | None:
        """The URL of the course in the LMS."""
        ai = self.application_instances[0]
        if ai.family != Family.CANVAS:
            # We only support Canvas for now
            return None

        if not ai.lms_url or not self.lms_api_course_id:
            # We need both the LMS base URL and the course ID
            return None

        return urljoin(ai.lms_url, f"/courses/{self.lms_api_course_id}")


class LMSCourseApplicationInstance(CreatedUpdatedMixin, Base):
    """Record of on which installs (application instances) we have seen one course."""

    __tablename__ = "lms_course_application_instance"

    __table_args__ = (sa.UniqueConstraint("application_instance_id", "lms_course_id"),)

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    application_instance_id: Mapped[int] = mapped_column(
        sa.ForeignKey("application_instances.id", ondelete="cascade"), index=True
    )
    application_instance: Mapped[ApplicationInstance] = relationship()

    lms_course_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lms_course.id", ondelete="cascade"), index=True
    )
    lms_course: Mapped[LMSCourse] = relationship()


class LMSCourseMembership(CreatedUpdatedMixin, Base):
    """Membership information for courses we have acquired via LTI launches."""

    __tablename__ = "lms_course_membership"
    __table_args__ = (
        sa.UniqueConstraint("lms_course_id", "lms_user_id", "lti_role_id"),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    lms_course_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lms_course.id", ondelete="cascade"), index=True
    )
    lms_course: Mapped[LMSCourse] = relationship()

    lms_user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lms_user.id", ondelete="cascade"), index=True
    )
    lms_user: Mapped["LMSUser"] = relationship()

    lti_role_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lti_role.id", ondelete="cascade"),
        index=True,
    )
    lti_role: Mapped["LTIRole"] = relationship()
