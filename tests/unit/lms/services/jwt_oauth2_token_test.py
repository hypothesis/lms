from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest
from freezegun import freeze_time

from lms.services.jwt_oauth2_token import JWTOAuth2TokenService, factory
from tests import factories


class TestJWTOAuth2TokenServiceTest:
    @freeze_time("2022-04-04")
    def test_save_new_token(self, svc, lti_registration):
        token = svc.save(lti_registration, "SCOPES", "ACCESS_TOKEN", 3600)

        assert token.access_token == "ACCESS_TOKEN"
        assert token.received_at == datetime(2022, 4, 4, 0)
        assert token.expires_at == token.received_at + timedelta(seconds=3600)

    @freeze_time("2022-04-04")
    def test_save_existing_token(self, svc, lti_registration):
        existing_token = factories.JWTOAuth2Token(
            lti_registration=lti_registration,
            scopes="SCOPES",
            expires_at=datetime.now(),
        )

        token = svc.save(lti_registration, "SCOPES", "ACCESS_TOKEN", 3600)

        assert existing_token == token
        assert token.received_at == datetime(2022, 4, 4, 0)
        assert token.expires_at == datetime(2022, 4, 4, 1)

    @freeze_time("2022-04-04")
    def test_get(self, svc, lti_registration, db_session):
        existing_token = factories.JWTOAuth2Token(
            lti_registration=lti_registration,
            scopes="SCOPES",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        db_session.flush()

        token = svc.get(lti_registration, "SCOPES")

        assert existing_token == token

    @freeze_time("2022-04-04")
    def test_get_doesnt_return_expired(self, svc, lti_registration, db_session):
        factories.JWTOAuth2Token(
            lti_registration=lti_registration,
            scopes="SCOPES",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.flush()

        token = svc.get(lti_registration, "SCOPES")

        assert not token

    @freeze_time("2022-04-04")
    def test_get_return_expired_with_flag(self, svc, lti_registration, db_session):
        expired_token = factories.JWTOAuth2Token(
            lti_registration=lti_registration,
            scopes="SCOPES",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.flush()

        token = svc.get(lti_registration, "SCOPES", exclude_expired=False)

        assert token == expired_token

    @pytest.fixture
    def svc(self, db_session):
        return JWTOAuth2TokenService(db_session)


class TestFactory:
    def test_it(self, pyramid_request, JWTOAuth2TokenService):
        service = factory(sentinel.context, pyramid_request)

        JWTOAuth2TokenService.assert_called_once_with(pyramid_request.db)
        assert service == JWTOAuth2TokenService.return_value

    @pytest.fixture
    def JWTOAuth2TokenService(self, patch):
        return patch("lms.services.jwt_oauth2_token.JWTOAuth2TokenService")
