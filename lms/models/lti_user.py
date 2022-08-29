from typing import NamedTuple

from lms.models.h_user import HUser
from lms.validation import ValidationError


class LTIUser(NamedTuple):
    """An LTI user."""

    user_id: str
    """The user_id LTI launch parameter."""

    roles: str
    """The user's LTI roles."""

    tool_consumer_instance_guid: str
    """Unique ID of the LMS instance that this user belongs to."""

    display_name: str
    """The user's display name."""

    application_instance_id: int
    """ID of the application instance this user belongs to"""

    email: str = ""
    """The user's email address."""

    validation_error: ValidationError = None
    """Exception found while trying to construct a LTIUser from the request"""

    def __bool__(self):
        """
        Override the bool behaviour of LTIUser.

        In case when we want to return an "empty" LTIUser behave like false so checks like:

            `if request.lti_user:`

        produce the expected result.
        """
        # Behave as "falsy" if neither the user_id or application_instance are present
        return bool(
            self.user_id and self.application_instance_id and not self.validation_error
        )

    @property
    def h_user(self):
        """Return a models.HUser generated from this LTIUser."""
        return HUser.from_lti_user(self)

    @property
    def is_instructor(self):
        """Whether this user is an instructor."""
        return any(
            role in self.roles.lower()
            for role in ("administrator", "instructor", "teachingassistant")
        )

    @property
    def is_learner(self):
        """Whether this user is a learner."""
        return "learner" in self.roles.lower()

    @staticmethod
    def from_auth_params(application_instance, lti_core_schema):
        """Create an LTIUser from a LTIV11CoreSchema like dict."""
        return LTIUser(
            user_id=lti_core_schema["user_id"],
            application_instance_id=application_instance.id,
            roles=lti_core_schema["roles"],
            tool_consumer_instance_guid=lti_core_schema["tool_consumer_instance_guid"],
            display_name=display_name(
                lti_core_schema["lis_person_name_given"],
                lti_core_schema["lis_person_name_family"],
                lti_core_schema["lis_person_name_full"],
            ),
            email=lti_core_schema["lis_person_contact_email_primary"],
        )

    @staticmethod
    def from_validation_error(validation_error):
        return LTIUser(
            user_id=None,
            application_instance_id=None,
            roles=None,
            tool_consumer_instance_guid=None,
            display_name=None,
            email=None,
            validation_error=validation_error,
        )


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
