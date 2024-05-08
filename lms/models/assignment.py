import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class Assignment(CreatedUpdatedMixin, Base):
    """
    An assignment configuration.

    When an LMS doesn't support LTI content-item selection/deep linking (so it
    doesn't support storing an assignment's document URL in the LMS and passing
    it back to us in launch requests) then we store the document URL in the
    database instead.

    Each persisted Assignment object represents a DB-stored
    assignment configuration, with the
    ``(tool_consumer_instance_guid, resource_link_id)`` launch params
    identifying the LTI resource (module item or assignment) and the
    ``document_url`` being the URL of the document to be annotated.
    """

    __tablename__ = "assignment"
    __table_args__ = (
        sa.UniqueConstraint("resource_link_id", "tool_consumer_instance_guid"),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    resource_link_id = sa.Column(sa.Unicode, nullable=False)
    """The resource_link_id launch param of the assignment."""

    tool_consumer_instance_guid = sa.Column(sa.Unicode, nullable=False)
    """
    The tool_consumer_instance_guid launch param of the LMS.

    This is needed because resource_link_id's aren't guaranteed to be unique
    across different LMS's.
    """

    copied_from_id = sa.Column(
        sa.Integer(), sa.ForeignKey("assignment.id"), nullable=True
    )
    """ID of the assignment this one was copied from using the course copy feature in the LMS."""

    copies = sa.orm.relationship(
        "Assignment", backref=sa.orm.backref("copied_from", remote_side=[id])
    )
    """Assignment this one was copied from."""

    document_url: Mapped[str] = mapped_column(sa.Unicode, nullable=False)
    """The URL of the document to be annotated for this assignment."""

    extra: Mapped[MutableDict] = mapped_column(
        MutableDict.as_mutable(JSONB()),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    is_gradable: Mapped[bool] = mapped_column(
        sa.Boolean(),
        default=False,
        server_default=sa.sql.expression.false(),
        nullable=False,
    )
    """Whether this assignment is gradable or not."""

    title = sa.Column(sa.Unicode, nullable=True)
    """The resource link title from LTI params."""

    description = sa.Column(sa.Unicode, nullable=True)
    """The resource link description from LTI params."""

    deep_linking_uuid: Mapped[str | None] = mapped_column(sa.Unicode, nullable=True)
    """UUID that identifies the deep linking that created this assignment."""

    groupings = association_proxy("assignment_grouping", "grouping")
    """List of groupings this assigments is related to."""

    membership = sa.orm.relationship(
        "AssignmentMembership", lazy="dynamic", viewonly=True
    )

    def get_canvas_mapped_file_id(self, file_id):
        return self.extra.get("canvas_file_mappings", {}).get(file_id, file_id)

    def set_canvas_mapped_file_id(self, file_id, mapped_file_id):
        self.extra.setdefault("canvas_file_mappings", {})[file_id] = mapped_file_id
