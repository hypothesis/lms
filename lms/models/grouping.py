from enum import Enum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from lms.db import BASE
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.application_settings import ApplicationSettings

MAX_GROUP_NAME_LENGTH = 25


class Grouping(CreatedUpdatedMixin, BASE):
    class Type(str, Enum):
        COURSE = "course"
        CANVAS_SECTION = "canvas_section"
        CANVAS_GROUP = "canvas_group"
        BLACKBOARD_GROUP = "blackboard_group"
        D2L_GROUP = "d2l_group"

        # These are the LMS agnostic versions of the ones avobe.
        # They don't get stored in the DB but are meaningful in the codebase
        SECTION = "section"
        GROUP = "group"

    __tablename__ = "grouping"
    __mapper_args__ = {"polymorphic_on": "type"}
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
        #     sqlalchemy.exc.ProgrammingError: (psycopg2.errors.InvalidForeignKey)
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
        # Only certain values are allowed in the `type` column.
        sa.CheckConstraint(
            "type in ('course', 'canvas_section', 'canvas_group', 'blackboard_group', 'd2l_group')",
            name="grouping_type_must_be_a_valid_value",
        ),
    )

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )
    application_instance = sa.orm.relationship("ApplicationInstance")

    #: The authority_provided_id of the Group that was created for this Grouping in h's DB.
    authority_provided_id = sa.Column(sa.UnicodeText(), nullable=False)

    #: The id of the parent grouping that this grouping belongs to.
    #:
    #: For example if the grouping represents a Canvas section or group then parent_id
    #: will reference the grouping for the course that the section or group belongs to.
    parent_id = sa.Column(sa.Integer(), nullable=True)
    children = sa.orm.relationship(
        "Grouping",
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
    lms_name = sa.Column(sa.UnicodeText(), nullable=False)

    type = sa.Column(sa.Unicode(), nullable=False)

    settings = sa.Column(
        "settings",
        ApplicationSettings.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    extra = sa.Column(
        "extra",
        MutableDict.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    memberships = sa.orm.relationship("GroupingMembership", back_populates="grouping")

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
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.CANVAS_SECTION}


class CanvasGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.CANVAS_GROUP}


class BlackboardGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.BLACKBOARD_GROUP}


class D2LGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.D2L_GROUP}


class Course(Grouping):
    __mapper_args__ = {"polymorphic_identity": Grouping.Type.COURSE}


class GroupingMembership(CreatedUpdatedMixin, BASE):
    __tablename__ = "grouping_membership"
    grouping_id = sa.Column(
        sa.Integer(), sa.ForeignKey("grouping.id", ondelete="cascade"), primary_key=True
    )
    grouping = sa.orm.relationship("Grouping", back_populates="memberships")

    user_id = sa.Column(
        sa.Integer(), sa.ForeignKey("user.id", ondelete="cascade"), primary_key=True
    )

    user = sa.orm.relationship("User")
