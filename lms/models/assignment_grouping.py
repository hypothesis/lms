import sqlalchemy as sa

from lms.db import BASE
from lms.models._mixins import CreatedUpdatedMixin


class AssignmentGrouping(CreatedUpdatedMixin, BASE):
    """Model for associations between assignments and groupings."""

    __tablename__ = "assignment_grouping"

    assignment_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("assignment.id", ondelete="cascade"),
        primary_key=True,
    )
    assignment = sa.orm.relationship("Assignment", foreign_keys=[assignment_id])
    """The assignment."""

    grouping_id = sa.Column(
        sa.Integer(), sa.ForeignKey("grouping.id", ondelete="cascade"), primary_key=True
    )
    grouping = sa.orm.relationship("Grouping", foreign_keys=[grouping_id])
    """The grouping the assignment is a part of."""
