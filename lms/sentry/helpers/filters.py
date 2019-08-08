"""
Functions for filtering out events we don't want to report to Sentry.

Each function takes a :class:`lms.sentry.helpers.event.Event` argument and
returns ``True`` if the event should be reported to Sentry or ``False`` to
filter it out. Every filter function gets called for every event and if any one
filter returns ``False`` for a given event then the event is not reported.
"""

from lms.services import CanvasAPIAccessTokenError


def filter_canvas_api_access_token_error(event):
    """Filter out all CanvasAPIAccessTokenError's."""
    if isinstance(event.exception, CanvasAPIAccessTokenError):
        return False
    return True
