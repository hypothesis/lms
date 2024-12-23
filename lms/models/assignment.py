from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DynamicMapped, Mapped, mapped_column, relationship

from lms.db import Base, varchar_enum
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.grouping import Course, Grouping


class AutoGradingType(StrEnum):
    ALL_OR_NOTHING = "all_or_nothing"
    SCALED = "scaled"


class AutoGradingCalculation(StrEnum):
    CUMULATIVE = "cumulative"
    SEPARATE = "separate"


class AutoGradingConfig(Base):
    __tablename__ = "assignment_auto_grading_config"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    activity_calculation: Mapped[str | None] = varchar_enum(AutoGradingCalculation)
    grading_type: Mapped[str | None] = varchar_enum(AutoGradingType)

    required_annotations: Mapped[int] = mapped_column()
    required_replies: Mapped[int | None] = mapped_column()

    def asdict(self):
        return {
            "grading_type": self.grading_type,
            "activity_calculation": self.activity_calculation,
            "required_annotations": self.required_annotations,
            "required_replies": self.required_replies,
        }


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

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    resource_link_id: Mapped[str] = mapped_column(sa.Unicode)
    """The resource_link_id launch param of the assignment."""

    lti_v13_resource_link_id: Mapped[str | None] = mapped_column(sa.Unicode)
    """
    The LTI1.3 resource_link_id of the assignment.

    This will be often the same as value as resource_link_id but it might be different in:
        - LTI1.1 launches. Where this will be null.
        - Upgraded instances from LTI1.1 where we prefer the LTI1.1 value (if exposed by the LMS).
          In those cases resource_link_id will be the 1.1 value and we'll store here the 1.3 version.
    """

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

    title: Mapped[str | None] = mapped_column(sa.Unicode, index=True)
    """The resource link title from LTI params."""

    description: Mapped[str | None] = mapped_column(sa.Unicode)
    """The resource link description from LTI params."""

    deep_linking_uuid: Mapped[str | None] = mapped_column(sa.Unicode)
    """UUID that identifies the deep linking that created this assignment."""

    groupings: DynamicMapped[Grouping] = sa.orm.relationship(
        secondary="assignment_grouping", viewonly=True, lazy="dynamic"
    )
    """Any groupings (courses, sections, groups) we have seen this assignment in during a launch"""

    membership = sa.orm.relationship(
        "AssignmentMembership", lazy="dynamic", viewonly=True
    )

    course_id: Mapped[int | None] = mapped_column(sa.ForeignKey(Course.id), index=True)

    course: Mapped[Course | None] = relationship(Course)

    lis_outcome_service_url: Mapped[str | None] = mapped_column()
    """URL of the grading serivce relevant for this assignment.

    This is named lis_outcome_service_url in both the LTI1.1 and the Names and Roles 2.0 specs

    It's equivalent to the

    https://purl.imsglobal.org/spec/lti-ags/claim/endpoint/lineitem

    claim on LTI1.3
    """
    auto_grading_config_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("assignment_auto_grading_config.id", ondelete="cascade")
    )
    auto_grading_config = relationship("AutoGradingConfig")

    __table_args__ = (
        sa.UniqueConstraint("resource_link_id", "tool_consumer_instance_guid"),
        sa.Index(
            "ix__assignment_title_is_not_null",
            "title",
            postgresql_where=title.is_not(None),
        ),
    )

    def get_canvas_mapped_file_id(self, file_id):
        return self.extra.get("canvas_file_mappings", {}).get(file_id, file_id)

    def set_canvas_mapped_file_id(self, file_id, mapped_file_id):
        self.extra.setdefault("canvas_file_mappings", {})[file_id] = mapped_file_id
