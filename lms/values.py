"""Immutable value objects for use throughout the app."""
from typing import NamedTuple

__all__ = ("LTIUser", "HUser")


class LTIUser(NamedTuple):
    """An LTI user."""

    user_id: str
    """The user_id LTI launch parameter."""

    oauth_consumer_key: str
    """The oauth_consumer_key LTI launch parameter."""

    roles: str
    """The user's LTI roles."""

    @property
    def is_instructor(self):
        """Whether this user is an instructor."""
        return any(
            role in self.roles.lower()
            for role in ("administrator", "instructor", "teachingassistant")
        )


class HUser(NamedTuple):
    """
    An 'h' user.

    The lms app generates h user accounts that correspond to LMS users who
    launch activities using the app. These user accounts have auto-generated
    usernames.
    """

    authority: str
    """
    The authority which the user belongs to.

    This should always match ``settings["h_authority"]``
    """

    username: str
    """
    Generated username for h user.

    This is derived from the LMS userid.
    """

    display_name: str = ""
    """The display name for the user, generated from the LMS user's display name."""

    @property
    def userid(self):
        return f"acct:{self.username}@{self.authority}"
