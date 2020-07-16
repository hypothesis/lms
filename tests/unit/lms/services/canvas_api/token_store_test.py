from datetime import datetime

import pytest
from h_matchers import Any

from lms.models import OAuth2Token
from lms.services import CanvasAPIAccessTokenError
from lms.services.canvas_api import TokenStore


@pytest.mark.usefixtures("application_instance")
class TestTokenStore:
    @pytest.mark.parametrize("delete_token", (False, True))
    def test_save(
        self,
        token_store,
        db_session,
        application_instance,
        lti_user,
        delete_token,
        oauth_token,
    ):
        if delete_token:
            db_session.expunge(oauth_token)

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

    def test_get_returns_token_when_present(self, token_store, db_session, oauth_token):
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
