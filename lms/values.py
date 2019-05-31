"""Immutable value objects for use throughout the app."""
from typing import NamedTuple


__all__ = ("LTIUser",)


class LTIUser(NamedTuple):
    """An LTI user."""

    user_id: str
    """The user_id LTI launch parameter."""

    oauth_consumer_key: str
    """The oauth_consumer_key LTI launch parameter."""

    roles: str
    """The user's LTI roles."""
