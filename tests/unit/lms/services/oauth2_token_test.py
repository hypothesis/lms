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
                "application_instance_id": application_instance.id,
                "user_id": lti_user.user_id,
                "access_token": "access_token",
                "refresh_token": "refresh_token",
                "expires_in": 1234,
                "received_at": Any.instance_of(datetime),
            }
        )

    def test_get_returns_token_when_present(self, svc, oauth_token):
        result = svc.get()

        assert result == oauth_token

    @pytest.mark.parametrize("wrong_param", ("application_instance", "user_id"))
    def test_get_raises_OAuth2TokenError_with_no_token(
        self, db_session, wrong_param, application_instance, lti_user
    ):
        wrong_value = "WRONG"
        if wrong_param == "application_instance":
            application_instance.consumer_key = "WRONG"
            wrong_value = application_instance

        store = OAuth2TokenService(
            db_session,
            **{
                "application_instance": application_instance,
                "user_id": lti_user.user_id,
                wrong_param: wrong_value,
            }
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
    def svc(self, pyramid_request, application_instance):
        return OAuth2TokenService(
            pyramid_request.db,
            application_instance,
            pyramid_request.lti_user.user_id,
        )


class TestOAuth2TokenServiceFactory:
    def test_it(self, pyramid_request, application_instance_service):
        svc = oauth2_token_service_factory(mock.sentinel.context, pyramid_request)

        application_instance_service.get_current.assert_called_once()
        assert isinstance(svc, OAuth2TokenService)
