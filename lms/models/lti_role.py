from enum import Enum, unique

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property

from lms.db import BASE, varchar_enum


@unique
class RoleType(str, Enum):
    """Enum for the different types of role a user can have."""

    INSTRUCTOR = "instructor"
    LEARNER = "learner"
    ADMIN = "admin"

    @classmethod
    def parse_lti_role(cls, role):
        """Parse an LTI role string into one of our role types."""

        # We have to do this work around because Enums can't have private
        # attributes. They are just interpreted as extra values for the enum.
        return _RoleParser.parse_role(role)


class LTIRole(BASE):
    """Model for LTI role strings and our interpretation of them."""

    __tablename__ = "lti_role"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    _value = sa.Column("value", sa.UnicodeText(), nullable=False, unique=True)
    """The raw string from LTI params."""

    type = varchar_enum(RoleType)
    """Our interpretation of the value."""

    @hybrid_property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.type = RoleType.parse_lti_role(value)


class _RoleParser:
    """Close collaborator class for parsing roles."""

    @classmethod
    def parse_role(cls, role) -> RoleType:
        return (
            cls._parse_v13_role(role) or cls._parse_v11_role(role) or RoleType.LEARNER
        )

    _V11_INSTRUCTOR_STRINGS = (
        "instructor",
        "teachingassistant",
        "contentdeveloper",
        "faculty",
        "mentor",
        "staff",
    )

    @classmethod
    def _parse_v11_role(cls, role):
        role = role.lower()

        for string in cls._V11_INSTRUCTOR_STRINGS:
            if string in role:
                return RoleType.INSTRUCTOR

        if "learner" in role:
            return RoleType.LEARNER

        if "admin" in role:
            return RoleType.ADMIN

        return None

    _V13_PREFIX = "http://purl.imsglobal.org/vocab/lis/v2"
    _V13_ROLE_MAPPINGS = {
        # https://www.imsglobal.org/spec/lti/v1p3/#lis-vocabulary-for-context-roles
        # A.2.1 LIS vocabulary for system roles
        # Core system roles
        f"{_V13_PREFIX}/system/person#Administrator": RoleType.ADMIN,
        f"{_V13_PREFIX}/system/person#None": RoleType.LEARNER,
        # Non‑core system roles
        f"{_V13_PREFIX}/system/person#AccountAdmin": RoleType.ADMIN,
        f"{_V13_PREFIX}/system/person#Creator": RoleType.INSTRUCTOR,
        f"{_V13_PREFIX}/system/person#SysAdmin": RoleType.ADMIN,
        f"{_V13_PREFIX}/system/person#SysSupport": RoleType.ADMIN,
        f"{_V13_PREFIX}/system/person#User": RoleType.LEARNER,
        # A.2.2 LIS vocabulary for institution roles
        # Core institution roles
        f"{_V13_PREFIX}/institution/person#Administrator": RoleType.ADMIN,
        f"{_V13_PREFIX}/institution/person#Faculty": RoleType.INSTRUCTOR,
        f"{_V13_PREFIX}/institution/person#Guest": RoleType.LEARNER,
        f"{_V13_PREFIX}/institution/person#None": RoleType.LEARNER,
        f"{_V13_PREFIX}/institution/person#Other": RoleType.LEARNER,
        f"{_V13_PREFIX}/institution/person#Staff": RoleType.INSTRUCTOR,
        f"{_V13_PREFIX}/institution/person#Student": RoleType.LEARNER,
        # Non‑core institution roles
        f"{_V13_PREFIX}/institution/person#Alumni": RoleType.LEARNER,
        f"{_V13_PREFIX}/institution/person#Instructor": RoleType.INSTRUCTOR,
        f"{_V13_PREFIX}/institution/person#Learner": RoleType.LEARNER,
        f"{_V13_PREFIX}/institution/person#Member": RoleType.LEARNER,
        f"{_V13_PREFIX}/institution/person#Mentor": RoleType.INSTRUCTOR,
        f"{_V13_PREFIX}/institution/person#Observer": RoleType.LEARNER,
        f"{_V13_PREFIX}/institution/person#ProspectiveStudent": RoleType.LEARNER,
        # A.2.3 LIS vocabulary for context roles
        # Core context roles
        f"{_V13_PREFIX}/membership/Administrator": RoleType.ADMIN,
        f"{_V13_PREFIX}/membership/ContentDeveloper": RoleType.INSTRUCTOR,
        f"{_V13_PREFIX}/membership/Instructor": RoleType.INSTRUCTOR,
        # Look out for this weirdo!
        f"{_V13_PREFIX}/membership/Learner#Instructor": RoleType.INSTRUCTOR,
        f"{_V13_PREFIX}/membership/Learner": RoleType.LEARNER,
        f"{_V13_PREFIX}/membership/Mentor": RoleType.INSTRUCTOR,
        # Non‑core context roles
        f"{_V13_PREFIX}/membership/Manager": RoleType.INSTRUCTOR,
        f"{_V13_PREFIX}/membership/Member": RoleType.LEARNER,
        f"{_V13_PREFIX}/membership/Office": RoleType.INSTRUCTOR,
    }

    @classmethod
    def _parse_v13_role(cls, role):
        role = role.strip()

        # Save some time if we aren't going to match
        if not role.startswith(cls._V13_PREFIX):
            return None

        # Try a quick match
        if type_ := cls._V13_ROLE_MAPPINGS.get(role):
            return type_

        # Do a thorough prefix match
        for prefix, type_ in cls._V13_ROLE_MAPPINGS.items():
            if role.startswith(prefix):
                return type_

        return None
