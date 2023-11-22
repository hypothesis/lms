from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.services import EmailPrefs
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.views.email import EmailPreferencesViews, forbidden, unsubscribe, unsubscribed

pytestmark = pytest.mark.usefixtures("email_preferences_service")


def test_unsubscribe(pyramid_request, email_preferences_service):
    pyramid_request.params["token"] = sentinel.token

    result = unsubscribe(pyramid_request)

    email_preferences_service.unsubscribe.assert_called_once_with(sentinel.token)
    assert isinstance(result, HTTPFound)
    assert result.location == "http://example.com/email/unsubscribed"


@pytest.mark.parametrize("exception", [ExpiredJWTError, InvalidJWTError])
def test_unsubscribe_error(pyramid_request, email_preferences_service, exception):
    pyramid_request.params["token"] = sentinel.token
    email_preferences_service.unsubscribe.side_effect = exception

    result = unsubscribe(pyramid_request)

    assert result == {}


def test_unsubscribed(pyramid_request):
    assert not unsubscribed(pyramid_request)


def test_forbidden(pyramid_request):
    # pylint:disable=use-implicit-booleaness-not-comparison
    assert forbidden(pyramid_request) == {}


class TestEmailPreferencesViews:
    def test_preferences_redirect(self, views, remember, pyramid_request):
        remember.return_value = [("foo", "bar")]

        result = views.preferences_redirect()

        remember.assert_called_once_with(
            pyramid_request, pyramid_request.authenticated_userid
        )
        assert result == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": "http://example.com/email/preferences",
            }
        )
        assert result.headers["foo"] == "bar"

    def test_preferences(self, views, email_preferences_service, pyramid_request):
        result = views.preferences()

        email_preferences_service.get_preferences.assert_called_once_with(
            pyramid_request.authenticated_userid
        )
        assert result == {
            "preferences": email_preferences_service.get_preferences.return_value.days.return_value
        }

    def test_set_preferences(self, views, email_preferences_service, pyramid_request):
        pyramid_request.params = {
            "mon": "on",
            "wed": "on",
            "thu": "off",
            "fri": "on",
            "sun": "on",
            "foo": "bar",
        }

        result = views.set_preferences()

        email_preferences_service.set_preferences.assert_called_once_with(
            EmailPrefs(
                pyramid_request.authenticated_userid,
                mon=True,
                tue=False,
                wed=True,
                thu=False,
                fri=True,
                sat=False,
                sun=True,
            )
        )
        assert result == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": "http://example.com/email/preferences",
            }
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return EmailPreferencesViews(pyramid_request)

    @pytest.fixture(autouse=True)
    def remember(self, patch):
        return patch("lms.views.email.remember")
