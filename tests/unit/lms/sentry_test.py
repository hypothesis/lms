from unittest import mock

import pytest
from h_pyramid_sentry.event import Event

from lms.sentry import filter_canvas_api_access_token_error
from lms.services import CanvasAPIAccessTokenError


class TestFilterCanvasAPIAccessTokenError:
    def test_it_filters_canvas_api_access_token_error(self):
        event = exception_event(
            CanvasAPIAccessTokenError(
                "We don't have a Canvas API access token for this user"
            )
        )
        assert filter_canvas_api_access_token_error(event)

    def test_it_doesnt_filter_other_exception_events(self, unexpected_exception_event):
        assert not filter_canvas_api_access_token_error(unexpected_exception_event)


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
