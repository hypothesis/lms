from enum import StrEnum
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base, varchar_enum
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.json_settings import JSONSettings
from lms.models.lms_course import LMSCourse

if TYPE_CHECKING:
    from lms.models import Assignment

MAX_GROUP_NAME_LENGTH = 25


class Grouping(CreatedUpdatedMixin, Base):
    class Type(StrEnum):
        COURSE = "course"
        CANVAS_SECTION = "canvas_section"
        CANVAS_GROUP = "canvas_group"
        BLACKBOARD_GROUP = "blackboard_group"
        D2L_GROUP = "d2l_group"
        MOODLE_GROUP = "moodle_group"

        # These are the LMS agnostic versions of the ones above.
        # They don't get stored in the DB but are meaningful in the codebase
        SECTION = "section"
        GROUP = "group"

    __tablename__ = "grouping"
    __mapper_args__ = {"polymorphic_on": "type"}  # noqa: RUF012
    __table_args__ = (
        # Within a given application instance no two groupings should have the
        # same authority_provided_id.
        sa.UniqueConstraint("application_instance_id", "authority_provided_id"),
        # Within a given application instance no two groupings with the same
        # parent and type should have the same lms_id. Examples:
        #
        # * Two groupings can have the same lms_id if they belong to
        #   different parents. For example in Canvas two sections in different
        #   courses can have the same ID.
        #
        # * Even within the same parent two groupings can have the same lms_id
        #   if they have different types. For example in Canvas a section can
        #   have the same ID as a group in the same course.
        #
        # * But two Canvas sections in the same course can't have the same ID,
        #   nor can two groups in the same course.
        sa.UniqueConstraint("lms_id", "application_instance_id", "parent_id", "type"),
        # SQLAlchemy forced us to add this constraint in order to make the
        # ForeignKeyConstraint below work, otherwise you get this error:
        #
        #     sqlalchemy.exc.ProgrammingError: (psycopg2.errors.InvalidForeignKey)  # noqa: ERA001
        #     there is no unique constraint matching given keys for referenced
        #     table "grouping"
        sa.UniqueConstraint("id", "application_instance_id"),
        # application_instance_id is included in this foreign key so that a
        # child grouping must always have the same application_instance_id as
        # its parent grouping.
        sa.ForeignKeyConstraint(
            ["parent_id", "application_instance_id"],
            ["grouping.id", "grouping.application_instance_id"],
            ondelete="cascade",
        ),
        # Courses aren't allowed to have parents but every non-course grouping
        # *must* have a parent.
        sa.CheckConstraint(
            "(type='course' AND parent_id IS NULL) OR (type!='course' AND parent_id IS NOT NULL)",
            name="courses_must_NOT_have_parents_and_other_groupings_MUST_have_parents",
        ),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )
    application_instance = sa.orm.relationship("ApplicationInstance")

    #: The authority_provided_id of the Group that was created for this Grouping in h's DB.
    authority_provided_id: Mapped[str] = mapped_column(sa.UnicodeText())

    #: The id of the parent grouping that this grouping belongs to.
    #:
    #: For example if the grouping represents a Canvas section or group then parent_id
    #: will reference the grouping for the course that the section or group belongs to.
    parent_id = sa.Column(sa.Integer(), nullable=True)
    children = sa.orm.relationship(
        "Grouping",
        foreign_keys=[parent_id, application_instance_id],
        backref=sa.orm.backref(
            "parent",
            remote_side=[id, application_instance_id],
            overlaps="application_instance",
        ),
        overlaps="application_instance",
    )

    #: The LMS's ID for the grouping.
    #:
    #: For example for a course this is the value of the context_id launch param.
    #: For a Canvas section or group this is the value of the section or group's id
    #: from the Canvas API.
    #:
    #: lms_id may not be unique without `parent_id`. For example a Canvas instance may
    #: have multiple sections or groups with the same id in different courses. In this
    #: case multiple Grouping's would have the same lms_id but they will have different
    #: parent_id's.
    lms_id = sa.Column(sa.Unicode(), nullable=False)

    #: Full name given on the LMS (e.g. "A course name 101")
    lms_name: Mapped[str] = mapped_column(sa.UnicodeText(), index=True)

    type = varchar_enum(Type, nullable=False)

    settings: Mapped[JSONSettings] = mapped_column(
        JSONSettings.as_mutable(JSONB()),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    extra: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB()),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    memberships = sa.orm.relationship(
        "GroupingMembership", lazy="dynamic", viewonly=True, back_populates="grouping"
    )

    copied_from_id = sa.Column(
        sa.Integer(), sa.ForeignKey("grouping.id"), nullable=True
    )
    """ID of the course grouping this one was copied from using the course copy feature in the LMS."""

    @property
    def name(self):
        """Return an h-compatible group name."""
        name = self.lms_name.strip()

        if len(name) > MAX_GROUP_NAME_LENGTH:
            return name[: MAX_GROUP_NAME_LENGTH - 1].rstrip() + "…"

        return name

    def groupid(self, authority):
        return f"group:{self.authority_provided_id}@{authority}"


class CanvasSection(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.CANVAS_SECTION}  # noqa: RUF012


class CanvasGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.CANVAS_GROUP}  # noqa: RUF012


class BlackboardGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.BLACKBOARD_GROUP}  # noqa: RUF012


class D2LGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.D2L_GROUP}  # noqa: RUF012


class MoodleGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.MOODLE_GROUP}  # noqa: RUF012


class Course(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.COURSE}  # noqa: RUF012

    _assignments: Mapped[list["Assignment"]] = sa.orm.relationship(
        secondary="assignment_grouping", viewonly=True
    )
    """Assignments that belong to this course."""

    lms_course: Mapped[LMSCourse] = sa.orm.relationship(
        LMSCourse,
        primaryjoin="Grouping.authority_provided_id == foreign(LMSCourse.h_authority_provided_id)",
        backref=sa.orm.backref("course"),
    )

    def get_mapped_page_id(self, page_id):
        """
        Get a previously mapped page id in a course.

        Returns the original `page_id` if no mapped one can be found.
        """
        return self._get_course_copy_mapped_key("course_copy_page_mappings", page_id)

    def set_mapped_page_id(self, old_page_id, new_page_id):
        """Store the mapping between old_page and new_page_id for future launches."""
        self._set_course_copy_mapped_key(
            "course_copy_page_mappings", old_page_id, new_page_id
        )

    def get_mapped_file_id(self, file_id):
        """
        Get a previously mapped file id in a course.

        Returns the original `file_id` if no mapped one can be found.
        """
        return self._get_course_copy_mapped_key("course_copy_file_mappings", file_id)

    def set_mapped_file_id(self, old_file_id, new_file_id):
        """Store the mapping between old_file_id and new_file_id for future launches."""
        self._set_course_copy_mapped_key(
            "course_copy_file_mappings", old_file_id, new_file_id
        )

    def get_mapped_group_set_id(self, group_set_id):
        """
        Get a previously mapped group set id in a course.

        Returns the given `group_set_id` if no mapped one can be found.
        """
        return self._get_course_copy_mapped_key(
            "course_copy_group_set_mappings", group_set_id
        )

    def set_mapped_group_set_id(self, old_group_set_id, group_set_id):
        """Store a mapping between old_group set id and group_set_id for future launches."""
        self._set_course_copy_mapped_key(
            "course_copy_group_set_mappings", old_group_set_id, group_set_id
        )

    def _set_course_copy_mapped_key(self, key, old_id, new_id):
        self.extra.setdefault(key, {})[old_id] = new_id

    def _get_course_copy_mapped_key(self, key, id_):
        return self.extra.get(key, {}).get(id_, id_)


class GroupingMembership(CreatedUpdatedMixin, Base):
    __tablename__ = "grouping_membership"
    grouping_id = sa.Column(
        sa.Integer(), sa.ForeignKey("grouping.id", ondelete="cascade"), primary_key=True
    )
    grouping = sa.orm.relationship("Grouping", back_populates="memberships")

    user_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("user.id", ondelete="cascade"),
        primary_key=True,
        index=True,
    )

    user = sa.orm.relationship("User")
