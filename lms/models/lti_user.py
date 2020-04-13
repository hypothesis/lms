from typing import NamedTuple


class LTIUser(NamedTuple):
    """An LTI user."""

    user_id: str
    """The user_id LTI launch parameter."""

    oauth_consumer_key: str
    """The oauth_consumer_key LTI launch parameter."""

    roles: str
    """The user's LTI roles."""

    tool_consumer_instance_guid: str
    """Unique ID of the LMS instance that this user belongs to."""

    given_name: str
    """The user's given name from the lis_person_name_given LTI param."""

    family_name: str
    """The user's family name from the lis_person_name_family LTI param."""

    full_name: str
    """The user's full name from the lis_person_name_full LTI param."""

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
