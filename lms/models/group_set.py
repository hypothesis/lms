from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin

if TYPE_CHECKING:
    from lms.models import LMSCourse


class LMSGroupSet(CreatedUpdatedMixin, Base):
    """Group sets are different ways to divide a course's roster into groups.

    Segments that represent groups belong to one group set.

    Some LMS call this concept a "Group category" instead.
    """

    __tablename__ = "lms_group_set"

    __table_args__ = (UniqueConstraint("lms_course_id", "lms_id"),)

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    lms_id: Mapped[str] = mapped_column(index=True)
    """ID of this group set in the LMS"""

    name: Mapped[str] = mapped_column()
    """Name of this group set in the LMS"""

    lms_course_id: Mapped[int] = mapped_column(ForeignKey("lms_course.id"))
    """ID of the course this group set belongs to"""

    lms_course: Mapped["LMSCourse"] = relationship("LMSCourse")
