import sqlalchemy as sa

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class AssignmentGrouping(CreatedUpdatedMixin, Base):
    """Model for associations between assignments and groupings."""

    __tablename__ = "assignment_grouping"

    assignment_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("assignment.id", ondelete="cascade"),
        primary_key=True,
        index=True,
    )
    assignment = sa.orm.relationship(
        "Assignment", foreign_keys=[assignment_id], backref="assignment_grouping"
    )
    """The assignment."""

    grouping_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("grouping.id", ondelete="cascade"),
        primary_key=True,
        index=True,
    )
    grouping = sa.orm.relationship(
        "Grouping", foreign_keys=[grouping_id], backref="groupings"
    )
    """The grouping the assignment is a part of."""
