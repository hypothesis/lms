"""Models to represent courses.

These duplicate some of the information stored in Grouping and GroupingMembership, the main differences being:

    - One LMSCourse row per course, not one per (application_instance_id, course) like in Grouping.
    - One or more rows in LMSCourseApplicationInstance, one per install we have seen the course in.
    - LMSCourse membership stores role information, GroupingMembership doesn't.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


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

    h_authority_provided_id: Mapped[str] = mapped_column(unique=True, index=True)
    """The Group.authority_provided_id value in H. This is calculated hashing tool_consumer_instance_guid and lti_context_id together."""

    copied_from_id: Mapped[int | None] = mapped_column(sa.ForeignKey("lms_course.id"))
    """ID of the course grouping this one was copied from using the course copy feature in the LMS."""

    name: Mapped[str] = mapped_column(index=True)


class LMSCourseApplicationInstance(CreatedUpdatedMixin, Base):
    """Record of on which installs (application instances) we have seen one course."""

    __tablename__ = "lms_course_application_instance"

    __table_args__ = (sa.UniqueConstraint("application_instance_id", "lms_course_id"),)

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    application_instance_id: Mapped[int] = mapped_column(
        sa.ForeignKey("application_instances.id", ondelete="cascade"), index=True
    )

    lms_course_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lms_course.id", ondelete="cascade"), index=True
    )


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

    lms_user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lms_course.id", ondelete="cascade"), index=True
    )

    lti_role_id: Mapped[int] = mapped_column(
        sa.ForeignKey("lti_role.id", ondelete="cascade"),
        index=True,
    )
