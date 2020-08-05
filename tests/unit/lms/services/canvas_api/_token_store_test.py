from datetime import datetime

import pytest
from h_matchers import Any
from pytest import param

from lms.models import OAuth2Token
from lms.services import CanvasAPIAccessTokenError
from lms.services.canvas_api._token_store import TokenStore
from tests import factories


@pytest.mark.usefixtures("application_instance")
class TestTokenStore:
    @pytest.mark.usefixtures("oauth_token_in_db_or_not")
    def test_save(self, token_store, db_session, application_instance, lti_user):
        token_store.save(
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

    def test_get_returns_token_when_present(self, token_store, oauth_token):
        result = token_store.get()

        assert result == oauth_token

    @pytest.mark.parametrize("wrong_param", ("consumer_key", "user_id"))
    def test_get_raises_CanvasAPIAccessTokenError_with_no_token(
        self, db_session, wrong_param, application_instance, lti_user
    ):
        store = TokenStore(
            db_session,
            **{
                "consumer_key": application_instance.consumer_key,
                "user_id": lti_user.user_id,
                wrong_param: "WRONG",
            }
        )

        with pytest.raises(CanvasAPIAccessTokenError):
            store.get()

    @pytest.fixture(
        params=(param(True, id="token in db"), param(False, id="token not in db"))
    )
    def oauth_token_in_db_or_not(
        self, request, db_session, lti_user, application_instance
    ):
        """Get an OAuthToken which either is, or isn't in the DB."""
        oauth_token = factories.OAuth2Token.build(
            user_id=lti_user.user_id,
            consumer_key=application_instance.consumer_key,
            # Don't link to an application instance directly, or factoryboy
            # will add this token whether we like it or not
            application_instance=None,
        )

        if request.param:
            db_session.add(oauth_token)

        return oauth_token
