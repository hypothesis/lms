import sqlalchemy as sa

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class AssignmentMembership(CreatedUpdatedMixin, Base):
    """Model for users associations with assignments."""

    __tablename__ = "assignment_membership"

    assignment_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("assignment.id", ondelete="cascade"),
        primary_key=True,
    )
    assignment = sa.orm.relationship("Assignment", foreign_keys=[assignment_id])
    """The assignment the user is a member of."""

    user_id = sa.Column(
        sa.Integer(), sa.ForeignKey("user.id", ondelete="cascade"), primary_key=True
    )
    user = sa.orm.relationship("User", foreign_keys=[user_id])
    """The user who is a member."""

    lti_role_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("lti_role.id", ondelete="cascade"),
        primary_key=True,
        index=True,
    )
    lti_role = sa.orm.relationship("LTIRole", foreign_keys=[lti_role_id])
    """What role the user plays in the assignment."""
