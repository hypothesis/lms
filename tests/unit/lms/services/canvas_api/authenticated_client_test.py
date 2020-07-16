import json
from io import BytesIO
from unittest.mock import call, create_autospec, sentinel

import pytest
from h_matchers import Any
from requests import Request, Response

from lms.services import CanvasAPIAccessTokenError
from lms.services.canvas_api import (
    CanvasAPIAuthenticatedClient,
    CanvasAPIBasicClient,
    TokenStore,
)
from lms.services.canvas_api.authenticated_client import CanvasTokenResponseSchema
from lms.validation import ValidationError
from tests import factories


class TestCanvasTokenResponseSchema:
    @pytest.mark.parametrize("value", (-1, 0))
    def test_expires_in_must_be_positive(self, value):
        response = Response()
        response.raw = BytesIO(
            json.dumps({"access_token": "required", "expires_in": value}).encode(
                "utf-8"
            )
        )

        with pytest.raises(ValidationError):
            CanvasTokenResponseSchema(response).parse()


class TestCanvasAPIAuthenticatedClient:
    def test_send(self, api_client, basic_api, oauth_token):
        basic_api.make_request.return_value = Request("GET", "url")

        result = api_client.send("METHOD", "/path", sentinel.schema, sentinel.params)

        basic_api.make_request.assert_called_once_with(
            "METHOD", "/path", sentinel.schema, sentinel.params
        )

        Any.request.assert_on_comparison = True
        basic_api.send_and_validate.assert_called_once_with(
            Any.request.containing_headers(
                {"Authorization": f"Bearer {oauth_token.access_token}"}
            ),
            sentinel.schema,
        )

        assert result == basic_api.send_and_validate.return_value

    def test_send_refreshes_and_retries_for_CanvasAPIAccessTokenError(
        self, api_client, basic_api, oauth_token, token_response
    ):
        basic_api.send_and_validate.side_effect = (
            CanvasAPIAccessTokenError,  # The first call should fail
            token_response,  # Then we expect a refresh call
            "success",  # Then finally our successful content request
        )

        result = api_client.send("METHOD", "/path", sentinel.schema, sentinel.params)

        basic_api.send_and_validate.assert_has_calls(
            [
                call(Any(), sentinel.schema),
                call(Any(), CanvasTokenResponseSchema),
                call(
                    Any.request.containing_headers(
                        {"Authorization": "Bearer new_access_token"}
                    ),
                    sentinel.schema,
                ),
            ]
        )

        assert result == "success"

    def test_send_raises_CanvasAPIAccessTokenError_if_it_cannot_refresh(
        self, api_client, basic_api, oauth_token
    ):
        oauth_token.refresh_token = None
        basic_api.send_and_validate.side_effect = CanvasAPIAccessTokenError

        with pytest.raises(CanvasAPIAccessTokenError):
            api_client.send("METHOD", "/path", sentinel.schema, sentinel.params)

    def test_get_token(self, api_client, basic_api, token_store):
        api_client.get_token("authorization_code")

        basic_api.get_url.assert_called_once_with("login/oauth2/token", url_stub="")
        basic_api.send_and_validate.assert_called_once_with(
            Any.request(
                "POST",
                Any.url.matching("http://example.com/token_url").with_query(
                    {
                        "grant_type": "authorization_code",
                        "client_id": "sentinel.client_id",
                        "client_secret": "sentinel.client_secret",
                        "code": "authorization_code",
                        "redirect_uri": "sentinel.redirect_uri",
                        "replace_tokens": "True",
                    }
                ),
            ),
            CanvasTokenResponseSchema,
        )
        token_store.save.assert_called_once_with(
            "new_access_token", "new_refresh_token", "new_expires_in"
        )

    def test_get_refreshed_token(self, api_client, basic_api, token_store):
        api_client.get_refreshed_token("refresh_token")

        basic_api.get_url.assert_called_once_with("login/oauth2/token", url_stub="")

        basic_api.send_and_validate.assert_called_once_with(
            Any.request(
                "POST",
                Any.url.matching("http://example.com/token_url").with_query(
                    {
                        "grant_type": "refresh_token",
                        "client_id": "sentinel.client_id",
                        "client_secret": "sentinel.client_secret",
                        "refresh_token": "refresh_token",
                    }
                ),
            ),
            CanvasTokenResponseSchema,
        )

        token_store.save.assert_called_once_with(
            "new_access_token", "new_refresh_token", "new_expires_in"
        )

    @pytest.fixture
    def api_client(self, basic_api, token_store):
        return CanvasAPIAuthenticatedClient(
            basic_api=basic_api,
            token_store=token_store,
            client_id=sentinel.client_id,
            client_secret=sentinel.client_secret,
            redirect_uri=sentinel.redirect_uri,
        )

    @pytest.fixture
    def basic_api(self, token_response):
        basic_api = create_autospec(CanvasAPIBasicClient)

        basic_api.send_and_validate.return_value = token_response
        basic_api.get_url.return_value = "http://example.com/token_url"
        basic_api.make_request.return_value = Request("GET", "http://example.com")

        return basic_api

    @pytest.fixture
    def token_response(self):
        return {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": "new_expires_in",
        }

    @pytest.fixture
    def token_store(self, oauth_token):
        token_store = create_autospec(TokenStore)

        token_store.get.return_value = oauth_token

        return token_store

    @pytest.fixture
    def oauth_token(self):
        return factories.OAuth2Token()
