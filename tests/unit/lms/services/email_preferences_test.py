from datetime import timedelta
from unittest.mock import sentinel

import pytest

from lms.models import EmailUnsubscribe
from lms.services.email_preferences import (
    EmailPreferencesService,
    EmailPrefs,
    InvalidTokenError,
    TokenPayload,
    UnrecognisedURLError,
    factory,
)
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from tests import factories


class TestEmailPrefs:
    @pytest.mark.parametrize(
        "kwargs,expected_attrs",
        (
            (
                {},
                {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
            ),
            (
                {
                    "mon": False,
                    "tue": False,
                    "wed": False,
                    "thu": False,
                    "fri": False,
                    "sat": False,
                    "sun": False,
                },
                {
                    "mon": False,
                    "tue": False,
                    "wed": False,
                    "thu": False,
                    "fri": False,
                    "sat": False,
                    "sun": False,
                },
            ),
        ),
    )
    def test___init__(self, kwargs, expected_attrs):
        prefs = EmailPrefs(h_userid=sentinel.h_userid, **kwargs)

        assert prefs.h_userid == sentinel.h_userid
        for attr, value in expected_attrs.items():
            assert getattr(prefs, attr) == value

    def test_days(self):
        prefs = EmailPrefs(
            h_userid=sentinel.h_userid, mon=False, wed=False, fri=False, sun=False
        )

        days = prefs.days()

        assert days == {
            "mon": False,
            "tue": True,
            "wed": False,
            "thu": True,
            "fri": False,
            "sat": True,
            "sun": False,
        }


class TestEmailPreferencesService:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("unsubscribe_url", "unsubscribe"),
            ("preferences_url", "preferences"),
        ],
    )
    def test_url(self, svc, jwt_service, method, path):
        jwt_service.encode_with_secret.return_value = "TOKEN"

        url = getattr(svc, method)(sentinel.h_userid, sentinel.tag)

        jwt_service.encode_with_secret.assert_called_once_with(
            {"h_userid": sentinel.h_userid, "tag": sentinel.tag},
            "SECRET",
            lifetime=timedelta(days=30),
        )
        assert url == f"http://example.com/email/{path}?token=TOKEN"

    def test_unsubscribe(self, svc, bulk_upsert, db_session, user_preferences_service):
        svc.unsubscribe(sentinel.h_userid, sentinel.tag)

        bulk_upsert.assert_called_once_with(
            db_session,
            model_class=EmailUnsubscribe,
            values=[
                {
                    "h_userid": sentinel.h_userid,
                    "tag": sentinel.tag,
                }
            ],
            index_elements=["h_userid", "tag"],
            update_columns=["updated"],
        )

        user_preferences_service.set.assert_called_once_with(
            sentinel.h_userid,
            {
                "instructor_email_digests.days.mon": False,
                "instructor_email_digests.days.tue": False,
                "instructor_email_digests.days.wed": False,
                "instructor_email_digests.days.thu": False,
                "instructor_email_digests.days.fri": False,
                "instructor_email_digests.days.sat": False,
                "instructor_email_digests.days.sun": False,
            },
        )

    def test_decode(self, svc, jwt_service):
        jwt_service.decode_with_secret.return_value = {
            "h_userid": sentinel.h_userid,
            "tag": sentinel.tag,
        }

        token_payload = svc.decode("https://example.com?token=test_token")

        jwt_service.decode_with_secret.assert_called_once_with("test_token", "SECRET")
        assert token_payload == TokenPayload(sentinel.h_userid, sentinel.tag)

    @pytest.mark.parametrize(
        "url",
        ["https://example.com?foo=bar", "https://example.com", "http://["],
    )
    def test_decode_if_URL_is_unrecognised_or_invalid(self, svc, url):
        with pytest.raises(UnrecognisedURLError):
            svc.decode(url)

    @pytest.mark.parametrize(
        "exception_class",
        [ExpiredJWTError, InvalidJWTError],
    )
    def test_decode_if_token_is_invalid_or_expired(
        self, svc, jwt_service, exception_class
    ):
        jwt_service.decode_with_secret.side_effect = exception_class

        with pytest.raises(InvalidTokenError):
            svc.decode("https://example.com?token=test_token")

    def test_get_preferences(self, svc, user_preferences_service):
        user_preferences_service.get.return_value = factories.UserPreferences(
            h_userid=sentinel.h_userid,
            preferences={
                "instructor_email_digests.days.mon": True,
                "instructor_email_digests.days.tue": False,
            },
        )

        preferences = svc.get_preferences(sentinel.h_userid)

        user_preferences_service.get.assert_called_once_with(sentinel.h_userid)
        assert preferences == EmailPrefs(
            h_userid=sentinel.h_userid, mon=True, tue=False
        )

    def test_set_preferences(self, svc, user_preferences_service):
        svc.set_preferences(EmailPrefs(sentinel.h_userid, tue=True, wed=False))

        user_preferences_service.set.assert_called_once_with(
            sentinel.h_userid,
            {
                "instructor_email_digests.days.mon": True,
                "instructor_email_digests.days.tue": True,
                "instructor_email_digests.days.wed": False,
                "instructor_email_digests.days.thu": True,
                "instructor_email_digests.days.fri": True,
                "instructor_email_digests.days.sat": True,
                "instructor_email_digests.days.sun": True,
            },
        )

    @pytest.fixture
    def svc(self, db_session, jwt_service, pyramid_request, user_preferences_service):
        return EmailPreferencesService(
            db_session,
            "SECRET",
            pyramid_request.route_url,
            jwt_service,
            user_preferences_service,
        )

    @pytest.fixture
    def bulk_upsert(self, patch):
        return patch("lms.services.email_preferences.bulk_upsert")


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        EmailPreferencesService,
        db_session,
        jwt_service,
        user_preferences_service,
    ):
        svc = factory(sentinel.context, pyramid_request)

        EmailPreferencesService.assert_called_once_with(
            db_session,
            secret="test_secret",
            route_url=pyramid_request.route_url,
            jwt_service=jwt_service,
            user_preferences_service=user_preferences_service,
        )
        assert svc == EmailPreferencesService.return_value

    @pytest.fixture
    def EmailPreferencesService(self, patch):
        return patch("lms.services.email_preferences.EmailPreferencesService")
