from unittest import mock

import pytest

from lms.sentry.helpers import filters
from lms.sentry.helpers.event import Event
from lms.services import CanvasAPIAccessTokenError


class TestFilterCanvasAPIAccessTokenError(object):
    def test_it_filters_canvas_api_access_token_error(self):
        event = exception_event(
            CanvasAPIAccessTokenError(
                "We don't have a Canvas API access token for this user"
            )
        )
        assert filters.filter_canvas_api_access_token_error(event) is False

    def test_it_doesnt_filter_other_exception_events(self, unexpected_exception_event):
        assert (
            filters.filter_canvas_api_access_token_error(unexpected_exception_event)
            is True
        )


@pytest.fixture
def unexpected_exception_event():
    """Return an unexpected exception event that no filter should stop."""
    return exception_event(ValueError("Unexpected!"))


def exception_event(exception):
    """
    Return an exception event for the given exception object.

    Return a mock :class:`lms.sentry.helpers.event.Event` of the kind that's
    created when some code raises an exception.
    """
    event = _event()
    event.exception = exception
    return event


def _event():
    """Return a mock :class:`lms.sentry.helpers.event.Event`."""
    return mock.create_autospec(Event, instance=True, spec_set=True)
