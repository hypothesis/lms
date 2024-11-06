from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base, varchar_enum
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.grouping import Grouping

if TYPE_CHECKING:
    from lms.models import LMSCourse, LMSUser, LTIRole


class LMSSegment(CreatedUpdatedMixin, Base):
    """Segments represent subdivisions of students in a course (i.e sections and groups)."""

    __tablename__ = "lms_segment"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    type = varchar_enum(Grouping.Type, nullable=False)

    lms_id: Mapped[str] = mapped_column(index=True)
    """ID of this segment in the LMS"""

    name: Mapped[str] = mapped_column()

    h_authority_provided_id: Mapped[str] = mapped_column(unique=True, index=True)
    """The Group.authority_provided_id value in H."""

    lms_course_id: Mapped[int | None] = mapped_column(ForeignKey("lms_course.id"))
    """ID of the course this segment belongs to"""
    lms_course: Mapped["LMSCourse"] = relationship()

    lms_group_set_id: Mapped[int | None] = mapped_column(
        ForeignKey("lms_group_set.id", ondelete="cascade"), index=True
    )
    """For groups, the group set they belong to"""


class LMSSegmentMembership(CreatedUpdatedMixin, Base):
    """Membership information we have acquired via LTI launches."""

    __tablename__ = "lms_segment_membership"
    __table_args__ = (UniqueConstraint("lms_segment_id", "lms_user_id", "lti_role_id"),)

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    lms_segment_id: Mapped[int] = mapped_column(
        ForeignKey("lms_segment.id", ondelete="cascade"), index=True
    )
    lms_segment: Mapped[LMSSegment] = relationship()

    lms_user_id: Mapped[int] = mapped_column(
        ForeignKey("lms_user.id", ondelete="cascade"), index=True
    )
    lms_user: Mapped["LMSUser"] = relationship()

    lti_role_id: Mapped[int] = mapped_column(
        ForeignKey("lti_role.id", ondelete="cascade"),
        index=True,
    )
    lti_role: Mapped["LTIRole"] = relationship()
