from unittest.mock import sentinel

import pytest

from lms.services.d2l_api._basic import API_VERSION, TOKEN_URL, BasicClient
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
from tests import factories


class TestBasicClient:
    def test_get_token(self, basic_client, oauth_http_service):
        basic_client.get_token(sentinel.authorization_code)

        oauth_http_service.get_access_token.assert_called_once_with(
            token_url=TOKEN_URL,
            redirect_uri=sentinel.redirect_uri,
            auth=(sentinel.client_id, sentinel.client_secret),
            authorization_code=sentinel.authorization_code,
        )

    def test_refresh_access_token(self, basic_client, oauth_http_service):
        basic_client.refresh_access_token()

        oauth_http_service.refresh_access_token.assert_called_once_with(
            TOKEN_URL,
            sentinel.redirect_uri,
            auth=(sentinel.client_id, sentinel.client_secret),
        )

    @pytest.mark.parametrize(
        "path,expected_url",
        [
            ("/foo/bar", f"https://d2l.example.com/d2l/api/lp/{API_VERSION}/foo/bar"),
            ("https://full.d2l.url.com/foo", "https://full.d2l.url.com/foo"),
        ],
    )
    def test_request_sends_the_request_and_returns_the_response(
        self, basic_client, oauth_http_service, path, expected_url
    ):
        response = basic_client.request("GET", path)

        oauth_http_service.request.assert_called_once_with("GET", expected_url)
        assert response == oauth_http_service.request.return_value

    def test_request_raises_ExternalRequestError_if_the_request_fails(
        self, basic_client, oauth_http_service
    ):
        oauth_http_service.request.side_effect = ExternalRequestError

        with pytest.raises(ExternalRequestError) as exc_info:
            basic_client.request("GET", "/foo")

        assert not exc_info.value.refreshable

    def test_request_raises_OAuth2TokenError_if_the_request_fails_with_an_access_token_error(
        self, basic_client, oauth_http_service
    ):
        oauth_http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(
                status_code=403, json_data={"Error": "Insufficient scope to call"}
            )
        )

        with pytest.raises(OAuth2TokenError) as exc_info:
            basic_client.request("GET", "/foo")

        assert not exc_info.value.refreshable

    @pytest.fixture
    def basic_client(self, http_service, oauth_http_service):
        return BasicClient(
            lms_host="d2l.example.com",
            client_id=sentinel.client_id,
            client_secret=sentinel.client_secret,
            redirect_uri=sentinel.redirect_uri,
            http_service=http_service,
            oauth_http_service=oauth_http_service,
        )
