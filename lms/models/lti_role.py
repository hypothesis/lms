import logging
from enum import Enum, unique

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

    @classmethod
    def parse(cls, role):
        """Parse an LTI role string into one of our role types."""

        # We have to do this work around because Enums can't have private
        # attributes. They are just interpreted as extra values for the enum.
        return _RoleParser.parse_role(role)


@unique
class RoleScope(str, Enum):
    """Enum for the different scopes of a role."""

    COURSE = "course"
    """Context in the spec"""

    INSTITUTION = "institution"
    SYSTEM = "system"

    @classmethod
    def parse(cls, role):
        """Parse an LTI role string into one of our role scopes."""

        scopes_prefixes = {
            # LTI 1.1 https://www.imsglobal.org/specs/ltiv1p0/implementation-guide
            "urn:lti:sysrole:ims": cls.SYSTEM,
            "urn:lti:instrole:ims": cls.INSTITUTION,
            "urn:lti:role:ims": cls.COURSE,
            # LTI 1.3 https://www.imsglobal.org/spec/lti/v1p3/#role-vocabularies
            "http://purl.imsglobal.org/vocab/lti/system": cls.SYSTEM,
            "http://purl.imsglobal.org/vocab/lis/v2/system": cls.SYSTEM,
            "http://purl.imsglobal.org/vocab/lis/v2/institution": cls.INSTITUTION,
            "http://purl.imsglobal.org/vocab/lis/v2/membership": cls.COURSE,
        }
        for prefix, scope in scopes_prefixes.items():
            if role.startswith(prefix):
                return scope

        # Non scoped roles are deprecated but allowed in LTI 1.3
        # Conforming implementations MAY recognize the simple names for context roles;
        # thus, for example, vendors can use the following roles interchangeably:
        #   http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor
        #   Instructor
        # However, support for simple names in this manner for context roles is deprecated;
        # by best practice, vendors should use the full URIs for all roles (context roles included).
        #
        # If we can't match any, pick the most restrictive
        return cls.COURSE


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
        self.type = RoleType.parse(value)
        self.scope = RoleScope.parse(value)


class _RoleParser:
    """Close collaborator class for parsing roles."""

    @classmethod
    def parse_role(cls, role) -> RoleType:
        if role := cls._parse_v13_role(role):
            return role

        # If we can't match any, pick the most restrictive
        LOG.debug("Can't find role type for %s", role)
        return RoleType.LEARNER

    _V13_ROLE_MAPPINGS = {
        "Administrator": RoleType.ADMIN,
        "ContentDeveloper": RoleType.INSTRUCTOR,
        "Instructor": RoleType.INSTRUCTOR,
        "Learner": RoleType.LEARNER,
        # Look out for this weirdo!
        "Learner#Instructor": RoleType.INSTRUCTOR,
        "Manager": RoleType.INSTRUCTOR,
        "Member": RoleType.LEARNER,
        "Mentor": RoleType.INSTRUCTOR,
        "Office": RoleType.INSTRUCTOR,
        "Grader": RoleType.INSTRUCTOR,
        "Staff": RoleType.INSTRUCTOR,
        "Faculty": RoleType.INSTRUCTOR,
        "SysAdmin": RoleType.ADMIN,
        "TeachingAssistant": RoleType.INSTRUCTOR,
        "person#AccountAdmin": RoleType.ADMIN,
        "person#Administrator": RoleType.ADMIN,
        "person#Alumni": RoleType.LEARNER,
        "person#Creator": RoleType.INSTRUCTOR,
        "person#Faculty": RoleType.INSTRUCTOR,
        "person#Guest": RoleType.LEARNER,
        "person#Instructor": RoleType.INSTRUCTOR,
        "person#Learner": RoleType.LEARNER,
        "person#Member": RoleType.LEARNER,
        "person#Mentor": RoleType.INSTRUCTOR,
        "person#None": RoleType.LEARNER,
        "person#Observer": RoleType.LEARNER,
        "person#Other": RoleType.LEARNER,
        "person#ProspectiveStudent": RoleType.LEARNER,
        "person#Staff": RoleType.INSTRUCTOR,
        "person#Student": RoleType.LEARNER,
        "person#SysAdmin": RoleType.ADMIN,
        "person#SysSupport": RoleType.ADMIN,
        "person#User": RoleType.LEARNER,
    }

    @classmethod
    def _parse_v13_role(cls, role):
        role = role.strip()
        role_mapping = dict(
            sorted(
                cls._V13_ROLE_MAPPINGS.items(), key=lambda x: len(x[0]), reverse=True
            )
        )

        for suffix, type_ in role_mapping.items():
            if role.endswith(suffix):
                return type_

        return None
