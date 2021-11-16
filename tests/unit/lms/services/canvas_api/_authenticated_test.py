from unittest.mock import call, create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.services import CanvasAPIServerError, OAuth2TokenError
from lms.services.canvas_api._basic import BasicClient
from lms.validation.authentication import OAuthTokenResponseSchema
from tests import factories


class TestAuthenticatedClient:
    def test_send(self, authenticated_client, basic_client, oauth_token):
        result = authenticated_client.send(
            "METHOD", "/path", sentinel.schema, params=sentinel.params
        )

        basic_client.send.assert_called_once_with(
            "METHOD",
            "/path",
            sentinel.schema,
            (10, 10),
            sentinel.params,
            headers={"Authorization": f"Bearer {oauth_token.access_token}"},
        )

        assert result == basic_client.send.return_value

    def test_send_raises_ProxyAPIAccessTokenError_if_we_dont_have_an_access_token_for_the_user(
        self, authenticated_client, oauth2_token_service
    ):
        oauth2_token_service.get.side_effect = OAuth2TokenError()

        with pytest.raises(OAuth2TokenError) as exc_info:
            authenticated_client.send(
                "METHOD", "/path", sentinel.schema, sentinel.params
            )

        assert exc_info.value.response is None

    def test_send_refreshes_and_retries_for_ProxyAPIAccessTokenError(
        self, authenticated_client, basic_client, token_response, oauth_token
    ):
        basic_client.send.side_effect = (
            OAuth2TokenError,  # The first call should fail
            token_response,  # Then we expect a refresh call
            "success",  # Then finally our successful content request
        )

        call_args = ("METHOD", "/path", sentinel.schema, (10, 10), sentinel.params)
        result = authenticated_client.send(*call_args)

        assert basic_client.send.call_args_list == [
            # Initial call with access token
            call(
                *call_args,
                headers={"Authorization": f"Bearer {oauth_token.access_token}"},
            ),
            # Refresh after the one above fails
            call(
                "POST",
                "login/oauth2/token",
                url_stub="",
                params=Any.mapping.containing(
                    {"refresh_token": oauth_token.refresh_token}
                ),
                schema=OAuthTokenResponseSchema,
                timeout=(10, 10),
            ),
            # Repeat call with new access token
            call(
                *call_args,
                headers={"Authorization": "Bearer new_access_token"},
            ),
        ]

        assert result == "success"

    def test_send_raises_ProxyAPIAccessTokenError_if_it_cannot_refresh(
        self, authenticated_client, basic_client, oauth_token
    ):
        oauth_token.refresh_token = None
        basic_client.send.side_effect = OAuth2TokenError

        with pytest.raises(OAuth2TokenError):
            authenticated_client.send(
                "METHOD", "/path", sentinel.schema, sentinel.params
            )

    def test_get_token(
        self, authenticated_client, basic_client, oauth2_token_service, token_response
    ):
        token = authenticated_client.get_token("authorization_code")

        assert token == "new_access_token"

        basic_client.send.assert_called_once_with(
            "POST",
            "login/oauth2/token",
            url_stub="",
            params={
                "grant_type": "authorization_code",
                "client_id": sentinel.client_id,
                "client_secret": sentinel.client_secret,
                "code": "authorization_code",
                "redirect_uri": sentinel.redirect_uri,
                "replace_tokens": True,
            },
            schema=OAuthTokenResponseSchema,
            timeout=(10, 10),
        )

        oauth2_token_service.save.assert_called_once_with(
            token_response["access_token"],
            token_response["refresh_token"],
            token_response["expires_in"],
        )

    def test_get_refreshed_token(
        self, authenticated_client, basic_client, oauth2_token_service, token_response
    ):
        token = authenticated_client.get_refreshed_token("refresh_token")

        assert token == "new_access_token"

        basic_client.send.assert_called_once_with(
            "POST",
            "login/oauth2/token",
            url_stub="",
            params={
                "grant_type": "refresh_token",
                "client_id": sentinel.client_id,
                "client_secret": sentinel.client_secret,
                "refresh_token": "refresh_token",
            },
            schema=OAuthTokenResponseSchema,
            timeout=(10, 10),
        )

        oauth2_token_service.save.assert_called_once_with(
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
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=token_response
        )
        token = token_method("code")
        assert token == token_response["access_token"]

    def test_invalid_access_token_response(
        self, token_method, http_session, token_response
    ):
        del token_response["access_token"]

        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=dict(token_response)
        )

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
