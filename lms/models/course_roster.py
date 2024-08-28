from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class CourseRoster(Base, CreatedUpdatedMixin):
    __tablename__ = "course_roster"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    lms_course_id: Mapped[int] = mapped_column(
        ForeignKey("lms_course.id", ondelete="cascade")
    )
    lms_course = relationship("LMSCourse")

    lms_user_id: Mapped[int] = mapped_column(
        ForeignKey("lms_user.id", ondelete="cascade")
    )
    lms_user = relationship("LMSUser")

    lti_role_id: Mapped[int] = mapped_column(
        ForeignKey("lti_role.id", ondelete="cascade")
    )
    lti_role = relationship("LTIRole")

    active: Mapped[bool] = mapped_column()

    __table_args__ = (UniqueConstraint("lms_course_id", "lms_user_id", "lti_role_id"),)
