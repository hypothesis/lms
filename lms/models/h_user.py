import hashlib
from typing import NamedTuple


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

    This should always match the h_authority setting.
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

    @classmethod
    def from_lti_user(cls, lti_user, authority):
        provider = lti_user.tool_consumer_instance_guid
        provider_unique_id = lti_user.user_id

        def username():
            """Return the h username for the current request."""
            username_hash_object = hashlib.sha1()
            username_hash_object.update(provider.encode())
            username_hash_object.update(provider_unique_id.encode())
            return username_hash_object.hexdigest()[:30]

        return cls(
            authority=authority,
            username=username(),
            display_name=lti_user.display_name,
            provider=provider,
            provider_unique_id=provider_unique_id,
        )

    @property
    def userid(self):
        return f"acct:{self.username}@{self.authority}"
