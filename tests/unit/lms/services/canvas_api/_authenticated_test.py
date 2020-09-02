from unittest.mock import call, create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.services import CanvasAPIAccessTokenError, CanvasAPIServerError
from lms.services.canvas_api._authenticated import TokenResponseSchema
from lms.services.canvas_api._basic import BasicClient


class TestAuthenticatedClient:
    def test_send(self, authenticated_client, basic_client, oauth_token):
        result = authenticated_client.send(
            "METHOD", "/path", sentinel.schema, sentinel.params
        )

        basic_client.send.assert_called_once_with(
            "METHOD",
            "/path",
            sentinel.schema,
            sentinel.params,
            headers={"Authorization": f"Bearer {oauth_token.access_token}"},
        )

        assert result == basic_client.send.return_value

    def test_send_refreshes_and_retries_for_CanvasAPIAccessTokenError(
        self, authenticated_client, basic_client, token_response, oauth_token
    ):
        basic_client.send.side_effect = (
            CanvasAPIAccessTokenError,  # The first call should fail
            token_response,  # Then we expect a refresh call
            "success",  # Then finally our successful content request
        )

        call_args = ("METHOD", "/path", sentinel.schema, sentinel.params)
        result = authenticated_client.send(*call_args)

        basic_client.send.assert_has_calls(
            (
                # Initial call with access token
                call(
                    *call_args,
                    headers={"Authorization": f"Bearer {oauth_token.access_token}"},
                ),
                # Refresh after the one above fails
                call(
                    "POST",
                    "login/oauth2/token",
                    params=Any.mapping.containing(
                        {"refresh_token": oauth_token.refresh_token}
                    ),
                    schema=Any(),
                    url_stub=Any(),
                ),
                # Repeat call with new access token
                call(*call_args, headers={"Authorization": "Bearer new_access_token"}),
            )
        )

        assert result == "success"

    def test_send_raises_CanvasAPIAccessTokenError_if_it_cannot_refresh(
        self, authenticated_client, basic_client, oauth_token
    ):
        oauth_token.refresh_token = None
        basic_client.send.side_effect = CanvasAPIAccessTokenError

        with pytest.raises(CanvasAPIAccessTokenError):
            authenticated_client.send(
                "METHOD", "/path", sentinel.schema, sentinel.params
            )

    def test_get_token(
        self, authenticated_client, basic_client, token_store, token_response
    ):
        token = authenticated_client.get_token("authorization_code")

        assert token == "new_access_token"

        basic_client.send.assert_called_once_with(
            "POST",
            "login/oauth2/token",
            params={
                "grant_type": "authorization_code",
                "client_id": sentinel.client_id,
                "client_secret": sentinel.client_secret,
                "code": "authorization_code",
                "redirect_uri": sentinel.redirect_uri,
                "replace_tokens": True,
            },
            schema=TokenResponseSchema,
            url_stub="",
        )

        token_store.save.assert_called_once_with(
            token_response["access_token"],
            token_response["refresh_token"],
            token_response["expires_in"],
        )

    def test_get_refreshed_token(
        self, authenticated_client, basic_client, token_store, token_response
    ):
        token = authenticated_client.get_refreshed_token("refresh_token")

        assert token == "new_access_token"

        basic_client.send.assert_called_once_with(
            "POST",
            "login/oauth2/token",
            params={
                "grant_type": "refresh_token",
                "client_id": sentinel.client_id,
                "client_secret": sentinel.client_secret,
                "refresh_token": "refresh_token",
            },
            schema=TokenResponseSchema,
            url_stub="",
        )

        token_store.save.assert_called_once_with(
            token_response["access_token"],
            token_response["refresh_token"],
            token_response["expires_in"],
        )

    @pytest.fixture
    def basic_client(self, token_response):
        basic_api = create_autospec(BasicClient)

        basic_api.send.return_value = token_response

        return basic_api


@pytest.mark.usefixtures("http_session")
class TestAuthenticatedClientIntegrated:
    """Tests which include the real basic client and Schema."""

    def test_ok(self, token_method, http_session, token_response):
        http_session.set_response(token_response)
        token = token_method("code")
        assert token == token_response["access_token"]

    @pytest.mark.parametrize("bad_value", [-1, 0, "string"])
    def test_bad_expires_in(
        self, token_method, http_session, token_response, bad_value
    ):
        http_session.set_response(dict(token_response, expires_in=bad_value))

        with pytest.raises(CanvasAPIServerError):
            token_method("code")

    @pytest.fixture(
        params=("get_token", "get_refreshed_token"),
        ids=("get_token", "get_refreshed_token"),
    )
    def token_method(self, request, authenticated_client):
        return getattr(authenticated_client, request.param)


@pytest.fixture
def token_response():
    return {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 384762,
    }
