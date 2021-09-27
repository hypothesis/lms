import logging
from datetime import datetime
from unittest import mock

import pytest
from h_matchers import Any
from pytest import param

from lms.models import OAuth2Token
from lms.services import OAuth2TokenError
from lms.services.oauth2_token import OAuth2TokenService, oauth2_token_service_factory
from tests import factories


@pytest.mark.usefixtures("application_instance")
class TestOAuth2TokenService:
    @pytest.mark.usefixtures("oauth_token_in_db_or_not")
    def test_save(self, svc, db_session, application_instance, lti_user):
        svc.save(
            access_token="access_token", refresh_token="refresh_token", expires_in=1234
        )

        oauth2_token = db_session.query(OAuth2Token).one()
        assert oauth2_token == Any.object(OAuth2Token).with_attrs(
            {
                "consumer_key": application_instance.consumer_key,
                "user_id": lti_user.user_id,
                "access_token": "access_token",
                "refresh_token": "refresh_token",
                "expires_in": 1234,
                "received_at": Any.instance_of(datetime),
            }
        )

    @pytest.mark.parametrize(
        "original_token,expect_log", [(None, False), ("token", True)]
    )
    def test_save_new_refresh_token(
        self,
        original_token,
        expect_log,
        svc,
        db_session,
        application_instance,
        lti_user,
        caplog,
    ):
        oauth_token = factories.OAuth2Token.build(
            user_id=lti_user.user_id,
            consumer_key=application_instance.consumer_key,
            application_instance=application_instance,
            refresh_token=original_token,
        )

        db_session.add(oauth_token)

        svc.save(
            access_token=oauth_token.access_token,
            refresh_token="NEW REFRESH TOKEN",
            expires_in=1234,
        )

        oauth2_token = db_session.query(OAuth2Token).one()

        assert oauth2_token.refresh_token == "NEW REFRESH TOKEN"
        if expect_log:
            assert caplog.record_tuples == [
                (
                    "lms.services.oauth2_token",
                    logging.WARNING,
                    f"Oauth2 refresh token new value for {oauth2_token.consumer_key}:{svc._user_id}",  # pylint:disable=protected-access
                )
            ]

    def test_get_returns_token_when_present(self, svc, oauth_token):
        result = svc.get()

        assert result == oauth_token

    @pytest.mark.parametrize("wrong_param", ("consumer_key", "user_id"))
    def test_get_raises_OAuth2TokenError_with_no_token(
        self, db_session, wrong_param, application_instance, lti_user
    ):
        store = OAuth2TokenService(
            db_session,
            **{
                "consumer_key": application_instance.consumer_key,
                "user_id": lti_user.user_id,
                wrong_param: "WRONG",
            },
        )

        with pytest.raises(OAuth2TokenError):
            store.get()

    @pytest.fixture(
        params=(param(True, id="token in db"), param(False, id="token not in db"))
    )
    def oauth_token_in_db_or_not(
        self, request, db_session, lti_user, application_instance
    ):
        """Get an OAuthToken or None based on the fixture params."""
        oauth_token = None
        if request.param:
            oauth_token = factories.OAuth2Token.build(
                user_id=lti_user.user_id,
                consumer_key=application_instance.consumer_key,
                application_instance=application_instance,
            )

            db_session.add(oauth_token)

        return oauth_token

    @pytest.fixture
    def svc(self, pyramid_request):
        return OAuth2TokenService(
            pyramid_request.db,
            pyramid_request.lti_user.oauth_consumer_key,
            pyramid_request.lti_user.user_id,
        )


class TestOAuth2TokenServiceFactory:
    def test_it(self, pyramid_request):
        svc = oauth2_token_service_factory(mock.sentinel.context, pyramid_request)

        assert isinstance(svc, OAuth2TokenService)
