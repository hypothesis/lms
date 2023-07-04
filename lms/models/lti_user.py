from dataclasses import dataclass
from typing import List, Optional

from lms.models.application_instance import ApplicationInstance
from lms.models.h_user import HUser
from lms.models.lti_role import LTIRole, RoleScope, RoleType


@dataclass
class LTI:
    course_id: str
    """ID of the course in the LMS, context_id using LTI naming"""

    assignment_id: Optional[str] = None
    """ID of the assignment in the LMS, resource_link_id using LTI naming"""


@dataclass
class LTIUser:  # pylint: disable=too-many-instance-attributes
    """An LTI user."""

    user_id: str
    """The user_id LTI launch parameter."""

    roles: str
    """The user's raw LTI roles string."""

    lti_roles: List[LTIRole]
    """The user's LTI roles."""

    tool_consumer_instance_guid: str
    """Unique ID of the LMS instance that this user belongs to."""

    display_name: str
    """The user's display name."""

    application_instance_id: int
    """ID of the application instance this user belongs to"""

    lti: LTI
    """
    Additional information about the LTI launch.

    Note that there's a bit of a backwards relationship here, we could have LTIUser inside LTI.

    LTIUser is now a central part of the authentication system so more ambitions changes require big refactors but
    there's an intention here to eventually replace the current:

    request.lti_user

    with something like:

    request.lti_session or similar with contains the user and any other relevant values.
    """

    application_instance: ApplicationInstance = None
    """Application instance this user belongs to"""

    email: str = ""
    """The user's email address."""

    @property
    def h_user(self):
        """Return a models.HUser generated from this LTIUser."""
        return HUser.from_lti_user(self)

    @property
    def is_instructor(self):
        """Whether this user is an instructor."""
        # We consider admins to be instructors for authorization purposes
        return self.is_admin or any(
            # And any instructor in the course
            role.type == RoleType.INSTRUCTOR and role.scope == RoleScope.COURSE
            for role in self.lti_roles
        )

    @property
    def is_learner(self):
        """Whether this user is a learner."""

        if self.is_instructor:
            return False

        return any(
            role.type == RoleType.LEARNER and role.scope == RoleScope.COURSE
            for role in self.lti_roles
        )

    @property
    def is_admin(self):
        """Whether this user is an admin."""
        return any(role.type == RoleType.ADMIN for role in self.lti_roles)


def display_name(given_name, family_name, full_name):
    """
    Return an h-compatible display name the given name parts.

    LTI 1.1 launch requests have separate given_name (lis_person_name_given),
    family_name (lis_person_name_family) and full_name (lis_person_name_full)
    parameters. This function returns a single display name string based on
    these three separate names.
    """
    name = full_name.strip()

    if not name:
        given_name = given_name.strip()
        family_name = family_name.strip()

        name = " ".join((given_name, family_name)).strip()

    if not name:
        return "Anonymous"

    # The maximum length of an h display name.
    display_name_max_length = 30

    if len(name) <= display_name_max_length:
        return name

    return name[: display_name_max_length - 1].rstrip() + "…"
