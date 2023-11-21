from datetime import timedelta
from unittest.mock import sentinel

import pytest

from lms.models import EmailUnsubscribe
from lms.services.email_preferences import (
    EmailPreferencesService,
    InvalidTokenError,
    UnrecognisedURLError,
    factory,
)
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError


class TestEmailPreferencesService:
    def test_unsubscribe_url(self, svc, jwt_service):
        jwt_service.encode_with_secret.return_value = "TOKEN"

        url = svc.unsubscribe_url(sentinel.email, sentinel.tag)

        jwt_service.encode_with_secret.assert_called_once_with(
            {"h_userid": sentinel.email, "tag": sentinel.tag},
            "SECRET",
            lifetime=timedelta(days=30),
        )
        assert url == "http://example.com/email/unsubscribe?token=TOKEN"

    def test_unsubscribe(self, svc, bulk_upsert, jwt_service, db_session):
        jwt_service.decode_with_secret.return_value = {
            "h_userid": sentinel.h_userid,
            "tag": sentinel.tag,
        }

        svc.unsubscribe(sentinel.token)

        jwt_service.decode_with_secret.assert_called_once_with(sentinel.token, "SECRET")
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

    def test_h_userid(self, svc, jwt_service):
        jwt_service.decode_with_secret.return_value = {"h_userid": sentinel.h_userid}

        h_userid = svc.h_userid("https://example.com?token=test_token")

        jwt_service.decode_with_secret.assert_called_once_with("test_token", "SECRET")
        assert h_userid == sentinel.h_userid

    @pytest.mark.parametrize(
        "url",
        ["https://example.com?foo=bar", "https://example.com", "http://["],
    )
    def test_h_userid_if_URL_is_unrecognised_or_invalid(self, svc, url):
        with pytest.raises(UnrecognisedURLError):
            svc.h_userid(url)

    @pytest.mark.parametrize(
        "exception_class",
        [ExpiredJWTError, InvalidJWTError],
    )
    def test_h_userid_if_token_is_invalid_or_expired(
        self, svc, jwt_service, exception_class
    ):
        jwt_service.decode_with_secret.side_effect = exception_class

        with pytest.raises(InvalidTokenError):
            svc.h_userid("https://example.com?token=test_token")

    @pytest.fixture
    def svc(self, db_session, jwt_service, pyramid_request):
        return EmailPreferencesService(
            db_session, jwt_service, "SECRET", pyramid_request.route_url
        )

    @pytest.fixture
    def bulk_upsert(self, patch):
        return patch("lms.services.email_preferences.bulk_upsert")


class TestFactory:
    def test_it(
        self, pyramid_request, EmailPreferencesService, db_session, jwt_service
    ):
        svc = factory(sentinel.context, pyramid_request)

        EmailPreferencesService.assert_called_once_with(
            db_session,
            jwt_service,
            secret="test_secret",
            route_url=pyramid_request.route_url,
        )
        assert svc == EmailPreferencesService.return_value

    @pytest.fixture
    def EmailPreferencesService(self, patch):
        return patch("lms.services.email_preferences.EmailPreferencesService")
