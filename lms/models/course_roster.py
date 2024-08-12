from sqlalchemy import ForeignKey, Unicode, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class CourseRoster(Base, CreatedUpdatedMixin):
    __tablename__ = "course_roster"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    authority_provided_id: Mapped[str] = mapped_column(Unicode, index=True)
    h_userid: Mapped[str] = mapped_column(Unicode, index=True)

    active: Mapped[bool] = mapped_column()

    lti_role_id: Mapped[int] = mapped_column(
        ForeignKey("lti_role.id", ondelete="cascade"),
        index=True,
    )
    lti_role = relationship("LTIRole")

    __table_args__ = (
        UniqueConstraint("authority_provided_id", "h_userid", "lti_role_id"),
    )
