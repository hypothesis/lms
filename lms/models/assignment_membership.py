from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class AssignmentMembership(CreatedUpdatedMixin, Base):
    """Model for users associations with assignments."""

    __tablename__ = "assignment_membership"

    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignment.id", ondelete="cascade"), primary_key=True, index=True
    )
    assignment = relationship("Assignment", foreign_keys=[assignment_id])
    """The assignment the user is a member of."""

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="cascade"), primary_key=True, index=True
    )
    user = relationship("User", foreign_keys=[user_id])
    """The user who is a member."""

    lti_role_id: Mapped[int] = mapped_column(
        ForeignKey("lti_role.id", ondelete="cascade"), primary_key=True, index=True
    )
    lti_role = relationship("LTIRole", foreign_keys=[lti_role_id])
    """What role the user plays in the assignment."""


class LMSUserAssignmentMembership(CreatedUpdatedMixin, Base):
    """Record of LMSUser that have launched one particular assignment.

    One row for each assignment, user and role.
    """

    __tablename__ = "lms_user_assignment_membership"
    __table_args__ = (UniqueConstraint("assignment_id", "lms_user_id", "lti_role_id"),)

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignment.id", ondelete="cascade"), index=True
    )
    assignment = relationship("Assignment", foreign_keys=[assignment_id])

    lms_user_id: Mapped[int] = mapped_column(
        ForeignKey("lms_user.id", ondelete="cascade"), index=True
    )
    lms_user = relationship("LMSUser", foreign_keys=[lms_user_id])

    lti_role_id: Mapped[int] = mapped_column(
        ForeignKey("lti_role.id", ondelete="cascade"),
        index=True,
    )
    lti_role = relationship("LTIRole", foreign_keys=[lti_role_id])
    """What role the user plays in the assignment."""

    lti_v11_lis_result_sourcedid: Mapped[str | None] = mapped_column()
    """LTI's lis_result_sourcedid, the relevant ID of one user in one assigment for the LTI1.1 grading API."""
