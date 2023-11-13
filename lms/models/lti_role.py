import logging
import re
from enum import Enum, unique
from typing import Tuple

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property

from lms.db import BASE, varchar_enum

LOG = logging.getLogger(__name__)


@unique
class RoleType(str, Enum):
    """Enum for the different types of role a user can have."""

    INSTRUCTOR = "instructor"
    LEARNER = "learner"
    ADMIN = "admin"


@unique
class RoleScope(str, Enum):
    """Enum for the different scopes of a role."""

    COURSE = "course"
    """Context in the spec"""

    INSTITUTION = "institution"
    SYSTEM = "system"


class LTIRoleOverride(BASE):
    __tablename__ = "lti_role_override"

    __table_args__ = (sa.UniqueConstraint("application_instance_id", "lti_role_id"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    lti_role_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("lti_role.id", ondelete="cascade"),
        nullable=True,
        index=True,
    )
    lti_role = sa.orm.relationship("LTIRole")

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )
    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="role_overrides"
    )

    type = varchar_enum(RoleType)
    """Our interpretation of the value."""

    scope = varchar_enum(RoleScope, nullable=True)
    """Scope where this role applies"""

    @property
    def value(self):
        return self.lti_role.value


class LTIRole(BASE):
    """Model for LTI role strings and our interpretation of them."""

    __tablename__ = "lti_role"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    _value = sa.Column("value", sa.UnicodeText(), nullable=False, unique=True)
    """The raw string from LTI params."""

    type = varchar_enum(RoleType)
    """Our interpretation of the value."""

    scope = varchar_enum(RoleScope, nullable=True)
    """Scope where this role applies"""

    @hybrid_property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.update_from_value()

    def update_from_value(self):
        """Set scope and type based on `_value`."""
        self.scope, self.type = _RoleParser.parse_role(self._value)


class _RoleParser:
    """Close collaborator class for parsing roles."""

    _ROLE_REGEXP = [
        # LTI 1.1 scoped role
        re.compile(r"urn:lti:(?P<scope>instrole|role|sysrole):ims/lis/(?P<type>\w+)"),
        # LTI 1.3 scoped role
        re.compile(
            r"http://purl.imsglobal.org/vocab/lis/v2/(?P<scope>membership|system|institution)#(?P<type>\w+)",
        ),
        # LTI 1.3 scoped with sub type
        re.compile(
            r"http://purl\.imsglobal\.org/vocab/lis/v2/(?P<scope>membership|system|institution)/(?P<type>\w+)#(?P<sub_type>\w+)"
        ),
        # https://www.imsglobal.org/spec/lti/v1p3/#lti-vocabulary-for-system-roles
        re.compile(
            r"http://purl\.imsglobal\.org/vocab/lti/(?P<scope>system)/(?P<type>\w+)#(?P<sub_type>\w+)",
        ),
        # Non scoped roles are deprecated but allowed in LTI 1.3
        # Conforming implementations MAY recognize the simple names for context
        # roles; thus, for example, vendors can use the following roles
        # interchangeably:
        #   http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor
        #   Instructor
        # However, support for simple names in this manner for context roles is
        # deprecated; by best practice, vendors should use the full URIs for
        # all roles (context roles included).
        re.compile(r"^(?!http|urn)(?P<type>\w+)"),
    ]

    _SCOPE_MAP = {
        # LTI 1.1 https://www.imsglobal.org/specs/ltiv1p0/implementation-guide
        "instrole": RoleScope.INSTITUTION,
        "role": RoleScope.COURSE,
        "sysrole": RoleScope.SYSTEM,
        # LTI 1.3 https://www.imsglobal.org/spec/lti/v1p3/#role-vocabularies
        "system": RoleScope.SYSTEM,
        "institution": RoleScope.INSTITUTION,
        "membership": RoleScope.COURSE,
    }
    _TYPE_MAP = {
        "AccountAdmin": RoleType.ADMIN,
        "Administrator": RoleType.ADMIN,
        "Alumni": RoleType.LEARNER,
        "ContentDeveloper": RoleType.INSTRUCTOR,
        "Creator": RoleType.INSTRUCTOR,
        "Faculty": RoleType.INSTRUCTOR,
        "Grader": RoleType.INSTRUCTOR,
        "Guest": RoleType.LEARNER,
        "Instructor": RoleType.INSTRUCTOR,
        "Learner": RoleType.LEARNER,
        "Manager": RoleType.INSTRUCTOR,
        "Member": RoleType.LEARNER,
        "Mentor": RoleType.INSTRUCTOR,
        "None": RoleType.LEARNER,
        "Observer": RoleType.LEARNER,
        "Office": RoleType.INSTRUCTOR,
        "Other": RoleType.LEARNER,
        "ProspectiveStudent": RoleType.LEARNER,
        "Staff": RoleType.INSTRUCTOR,
        "Student": RoleType.LEARNER,
        "SysAdmin": RoleType.ADMIN,
        "SysSupport": RoleType.ADMIN,
        "TeachingAssistant": RoleType.INSTRUCTOR,
        "User": RoleType.LEARNER,
    }

    @classmethod
    def parse_role(cls, role) -> Tuple[RoleScope, RoleType]:
        """Parse roles according to the expected values from the specs."""
        role_parts = {}
        for regex in cls._ROLE_REGEXP:
            if match := regex.match(role):
                role_parts = match.groupdict()
                break

        # No scope, default to the narrowest, COURSE
        scope = cls._SCOPE_MAP.get(role_parts.get("scope"), RoleScope.COURSE)

        # In system and institution roles the main type is "person"
        if role_parts.get("type") == "person":
            role_parts["type"] = role_parts["sub_type"]

        type_ = cls._TYPE_MAP.get(role_parts.get("type"), RoleType.LEARNER)

        return scope, type_
