from typing import NamedTuple

from lms.models._hashed_id import hashed_id


def get_h_username(guid: str, lms_user_id: str):
    return hashed_id(guid, lms_user_id)[:30]


def get_h_userid(authority: str, h_username: str):
    return f"acct:{h_username}@{authority}"


class HUser(NamedTuple):
    """
    An 'h' user.

    The lms app generates h user accounts that correspond to LMS users who
    launch activities using the app. These user accounts have auto-generated
    usernames.
    """

    username: str
    """
    Generated username for h user.

    This is derived from the LMS userid.
    """

    display_name: str = ""
    """The display name for the user, generated from the LMS user's display name."""

    provider: str = ""
    """The "provider" string to pass to the h API for this user."""

    provider_unique_id: str = ""
    """The "provider_unique_id" string to pass to the h API for this user."""

    def userid(self, authority):
        return get_h_userid(authority, self.username)

    @classmethod
    def from_lti_user(cls, lti_user):
        provider = lti_user.tool_consumer_instance_guid
        provider_unique_id = lti_user.user_id

        return cls(
            username=get_h_username(provider, provider_unique_id),
            display_name=lti_user.display_name,
            provider=provider,
            provider_unique_id=provider_unique_id,
        )
