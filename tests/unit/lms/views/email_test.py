from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.security import EmailPreferencesIdentity
from lms.services import EmailPreferences
from lms.views.email import EmailPreferencesViews, forbidden

pytestmark = pytest.mark.usefixtures("email_preferences_service")


def test_forbidden(pyramid_request):
    assert forbidden(pyramid_request) == {}


class TestEmailPreferencesViews:
    @pytest.mark.parametrize(
        "tag,expected_message",
        (
            (
                "instructor_digest",
                "You've been unsubscribed from student annotation email notifications.",
            ),
            ("mention", "You've been unsubscribed from mention emails."),
        ),
    )
    def test_unsubscribe(
        self,
        views,
        pyramid_config,
        email_preferences_service,
        remember,
        pyramid_request,
        tag,
        expected_message,
    ):
        remember.return_value = [("foo", "bar")]
        pyramid_config.testing_securitypolicy(
            userid=sentinel.h_userid,
            identity=EmailPreferencesIdentity(sentinel.h_userid, tag),
        )

        result = views.unsubscribe()

        email_preferences_service.unsubscribe.assert_called_once_with(
            sentinel.h_userid, tag
        )
        assert pyramid_request.session.pop_flash("email_preferences_result") == [
            expected_message
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
        preferences = email_preferences_service.get_preferences.return_value
        expected = {
            "jsConfig": {
                "mode": "email-preferences",
                "emailPreferences": {
                    "is_instructor": preferences.is_instructor,
                    "selectedDays": {
                        "mon": preferences.mon,
                        "tue": preferences.tue,
                        "wed": preferences.wed,
                        "thu": preferences.thu,
                        "fri": preferences.fri,
                        "sat": preferences.sat,
                        "sun": preferences.sun,
                    },
                    "mention_email_feature_enabled": preferences.mention_email_feature_enabled,
                    "mention_email_subscribed": preferences.mention_email_subscribed,
                    "flashMessage": flash_message,
                },
            }
        }
        assert result == expected

    @pytest.mark.parametrize("mention_email_feature_enabled", (True, False))
    @pytest.mark.parametrize("mention_email_subscribed_form", ("on", "off"))
    @pytest.mark.parametrize("is_instructor", (True, False))
    def test_set_preferences(
        self,
        views,
        email_preferences_service,
        pyramid_request,
        mention_email_feature_enabled,
        mention_email_subscribed_form,
        is_instructor,
    ):
        email_preferences_service.get_preferences.return_value = EmailPreferences(
            is_instructor=is_instructor,
            mention_email_feature_enabled=mention_email_feature_enabled,
            h_userid=pyramid_request.authenticated_userid,
        )
        pyramid_request.params = {
            "mon": "on",
            "wed": "on",
            "thu": "off",
            "fri": "on",
            "sun": "on",
            "foo": "bar",
            "mention_email_subscribed": mention_email_subscribed_form,
        }

        result = views.set_preferences()

        email_preferences_service.set_preferences.assert_called_once_with(
            EmailPreferences(
                pyramid_request.authenticated_userid,
                is_instructor=is_instructor,
                mention_email_feature_enabled=mention_email_feature_enabled,
                mention_email_subscribed=True
                if not mention_email_feature_enabled
                else mention_email_subscribed_form == "on",
                mon=True,
                tue=not is_instructor,
                wed=True,
                thu=not is_instructor,
                fri=True,
                sat=not is_instructor,
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
