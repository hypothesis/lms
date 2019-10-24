"""Immutable value objects for use throughout the app."""
from typing import NamedTuple

__all__ = ("LTIUser", "LISResultSourcedId")


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


class LISResultSourcedId(NamedTuple):
    """
    LIS Outcome metadata for an LMS student user.

    May be used—in combination with :class:`~lms.values.LTIUser` and
    :class:`~lms.values.HUser` to populate an :class:`lms.models.LISResultSourcedId`
    model.
    """

    lis_result_sourcedid: str
    """The LIS Result Identifier associated with this launch."""

    lis_outcome_service_url: str
    """Service URL for communicating outcomes."""

    context_id: str
    """unique id of the course from which the user is accessing the app."""

    resource_link_id: str
    """unique id referencing the link, or "placement", of the app in the consumer."""

    tool_consumer_info_product_family_code: str = ""
    """The 'family' of LMS tool, e.g. 'BlackboardLearn' or 'canvas'."""
