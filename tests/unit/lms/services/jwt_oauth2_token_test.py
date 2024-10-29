from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest
from freezegun import freeze_time

from lms.services.jwt_oauth2_token import JWTOAuth2TokenService, factory
from tests import factories


class TestJWTOAuth2TokenServiceTest:
    @freeze_time("2022-04-04")
    @pytest.mark.parametrize("scopes", [("1", "2"), ("2", "1")])
    def test_it(self, svc, lti_registration, scopes):
        token = svc.save_token(lti_registration, scopes, "ACCESS_TOKEN", 3600)

        assert svc.get_token(lti_registration, scopes) == token
        assert token.scopes == "1 2"

    @freeze_time("2022-04-04")
    def test_save_new_token(self, svc, lti_registration, scopes):
        token = svc.save_token(lti_registration, scopes, "ACCESS_TOKEN", 3600)

        assert token.access_token == "ACCESS_TOKEN"
        assert token.expires_at == datetime(2022, 4, 4) + timedelta(seconds=3600)

    @freeze_time("2022-04-04")
    def test_save_existing_token(self, svc, lti_registration, scopes):
        existing_token = factories.JWTOAuth2Token(
            lti_registration=lti_registration,
            scopes=" ".join(scopes),
            expires_at=datetime.now(),
        )

        token = svc.save_token(lti_registration, scopes, "ACCESS_TOKEN", 3600)

        assert existing_token == token
        assert token.expires_at == datetime(2022, 4, 4, 1)

    @freeze_time("2022-04-04")
    def test_get(self, svc, lti_registration, db_session, scopes):
        existing_token = factories.JWTOAuth2Token(
            lti_registration=lti_registration,
            scopes=" ".join(scopes),
            expires_at=datetime.now() + timedelta(hours=1),
        )
        db_session.flush()

        token = svc.get_token(lti_registration, scopes)

        assert existing_token == token

    @freeze_time("2022-04-04")
    def test_get_doesnt_return_expired(self, svc, lti_registration, db_session, scopes):
        factories.JWTOAuth2Token(
            lti_registration=lti_registration,
            scopes=" ".join(scopes),
            expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.flush()

        token = svc.get_token(lti_registration, scopes)

        assert not token

    @freeze_time("2022-04-04")
    def test_get_return_expired_with_flag(
        self, svc, lti_registration, db_session, scopes
    ):
        expired_token = factories.JWTOAuth2Token(
            lti_registration=lti_registration,
            scopes=" ".join(scopes),
            expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.flush()

        token = svc.get_token(lti_registration, scopes, exclude_expired=False)

        assert token == expired_token

    @pytest.fixture
    def scopes(self):
        return ["SCOPE_1", "SCOPE_2"]

    @pytest.fixture(autouse=True)
    def with_existing_group_infos(self):
        # Add some "noise" tokens to make the tests more realistic
        factories.JWTOAuth2Token.build_batch(3)

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
