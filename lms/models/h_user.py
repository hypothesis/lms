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

    @property
    def userid(self):
        return f"acct:{self.username}@{self.authority}"
