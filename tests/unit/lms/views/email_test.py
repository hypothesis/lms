from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.security import EmailPreferencesIdentity
from lms.services import EmailPrefs
from lms.views.email import EmailPreferencesViews, forbidden

pytestmark = pytest.mark.usefixtures("email_preferences_service")


def test_forbidden(pyramid_request):
    # pylint:disable=use-implicit-booleaness-not-comparison
    assert forbidden(pyramid_request) == {}


class TestEmailPreferencesViews:
    def test_unsubscribe(
        self,
        views,
        pyramid_config,
        email_preferences_service,
        remember,
        pyramid_request,
    ):
        remember.return_value = [("foo", "bar")]
        pyramid_config.testing_securitypolicy(
            userid=sentinel.h_userid,
            identity=EmailPreferencesIdentity(sentinel.h_userid, sentinel.tag),
        )

        result = views.unsubscribe()

        email_preferences_service.unsubscribe.assert_called_once_with(sentinel.h_userid)
        assert pyramid_request.session.pop_flash("email_preferences_result") == [
            "You've been unsubscribed from email notifications."
        ]
        remember.assert_called_once_with(
            pyramid_request, pyramid_request.authenticated_userid
        )
        assert result == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": "http://example.com/email/preferences",
            }
        )
        assert result.headers["foo"] == "bar"

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

    @pytest.mark.parametrize("flash_message", (None, "This is the result"))
    def test_preferences(
        self, views, email_preferences_service, pyramid_request, flash_message
    ):
        if flash_message:
            pyramid_request.session.flash(flash_message, "email_preferences_result")

        result = views.preferences()

        email_preferences_service.get_preferences.assert_called_once_with(
            pyramid_request.authenticated_userid
        )
        assert result == {
            "jsConfig": {
                "mode": "email-preferences",
                "emailPreferences": {
                    "selectedDays": email_preferences_service.get_preferences.return_value.days.return_value,
                    "flashMessage": flash_message,
                },
            }
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
        assert pyramid_request.session.peek_flash("email_preferences_result") == [
            "Preferences saved.",
        ]
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
