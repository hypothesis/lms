from unittest.mock import DEFAULT, call, sentinel

import pytest

from lms.services.blackboard_api._basic import (
    BasicClient,
    BlackboardErrorResponseSchema,
)
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
from tests import factories


class TestBlackboardErrorResponseSchema:
    @pytest.mark.parametrize(
        "input_,output",
        [
            (
                {"status": 401, "message": "Bearer token is invalid"},
                {"status": 401, "message": "Bearer token is invalid"},
            ),
            (
                {"status": "foo", "message": 42},
                {"status": "foo", "message": 42},
            ),
            (
                {"status": None, "message": None},
                {"status": None, "message": None},
            ),
            (
                {"message": "Bearer token is invalid"},
                {"message": "Bearer token is invalid"},
            ),
            ({"status": 401}, {"status": 401}),
            ({}, {}),
            ([], {}),
        ],
    )
    def test_it(self, input_, output):
        response = factories.requests.Response(json_data=input_)

        error_dict = BlackboardErrorResponseSchema(response).parse()

        assert error_dict == output

    def test_when_the_response_body_isnt_JSON(self):
        assert (
            BlackboardErrorResponseSchema(factories.requests.Response()).parse() == {}
        )

    def test_when_the_response_object_is_None(self):
        assert BlackboardErrorResponseSchema(None).parse() == {}


class TestBasicClientGetToken:
    def test_it(self, basic_client, oauth_http_service):
        basic_client.get_token(sentinel.authorization_code)

        oauth_http_service.get_access_token.assert_called_once_with(
            token_url="https://blackboard.example.com/learn/api/public/v1/oauth2/token",
            redirect_uri=sentinel.redirect_uri,
            auth=(sentinel.client_id, sentinel.client_secret),
            authorization_code=sentinel.authorization_code,
        )


class TestBasicClientRefreshAccessToken:
    def test_it(self, basic_client, oauth_http_service):
        basic_client.refresh_access_token()

        oauth_http_service.refresh_access_token.assert_called_once_with(
            "https://blackboard.example.com/learn/api/public/v1/oauth2/token",
            sentinel.redirect_uri,
            auth=(sentinel.client_id, sentinel.client_secret),
        )


class TestBasicClientRequest:
    @pytest.mark.parametrize(
        "path,expected_url",
        [
            ("foo/bar/", "https://blackboard.example.com/learn/api/public/v1/foo/bar/"),
            (
                "/learn/api/public/v1/foo/bar/",
                "https://blackboard.example.com/learn/api/public/v1/foo/bar/",
            ),
            ("/foo/bar/", "https://blackboard.example.com/foo/bar/"),
        ],
    )
    def test_it_sends_the_request_and_returns_the_response(
        self, basic_client, oauth_http_service, path, expected_url
    ):
        response = basic_client.request("GET", path)

        oauth_http_service.request.assert_called_once_with("GET", expected_url)
        assert response == oauth_http_service.request.return_value

    # If the request fails on first attempt request() sends a refresh token
    # request and then re-tries the original request.
    def test_it_refreshes_and_tries_again_if_the_first_request_fails(
        self, basic_client, oauth_http_service
    ):
        basic_client.refresh_enabled = True
        # Make the first attempt at the request fail but the second succeed.
        oauth_http_service.request.side_effect = [ExternalRequestError, DEFAULT]

        response = basic_client.request("GET", "/foo")

        assert oauth_http_service.request.call_args_list == [
            call("GET", "https://blackboard.example.com/foo"),
            call("GET", "https://blackboard.example.com/foo"),
        ]
        oauth_http_service.refresh_access_token.assert_called_once_with(
            token_url="https://blackboard.example.com/learn/api/public/v1/oauth2/token",
            redirect_uri=sentinel.redirect_uri,
            auth=(sentinel.client_id, sentinel.client_secret),
        )
        assert response == oauth_http_service.request.return_value

    # If the request fails on first attempt and then the refresh token request
    # also raises then request() raises.
    def test_it_raises_if_the_refresh_request_fails(
        self, basic_client, oauth_http_service
    ):
        # Make the API request fail.
        oauth_http_service.request.side_effect = ExternalRequestError
        # Make the refresh token request also fail.
        oauth_http_service.refresh_access_token.side_effect = ExternalRequestError

        with pytest.raises(ExternalRequestError):
            basic_client.request("GET", "/foo")

    # If both attempts at the API request fail then request() raises.
    def test_request_raises_if_the_second_request_fails(
        self, basic_client, oauth_http_service
    ):
        # Make the API request fail both times.
        oauth_http_service.request.side_effect = ExternalRequestError

        with pytest.raises(ExternalRequestError):
            basic_client.request("GET", "/foo")

    def test_it_raises_OAuth2TokenError_if_the_request_fails_with_an_access_token_error(
        self, basic_client, oauth_http_service
    ):
        # Make the API request fail both times.
        oauth_http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(
                json_data={"status": 401, "message": "Bearer token is invalid"}
            )
        )

        with pytest.raises(OAuth2TokenError):
            basic_client.request("GET", "/foo")


@pytest.fixture
def basic_client(http_service, oauth_http_service):
    return BasicClient(
        blackboard_host="blackboard.example.com",
        client_id=sentinel.client_id,
        client_secret=sentinel.client_secret,
        redirect_uri=sentinel.redirect_uri,
        http_service=http_service,
        oauth_http_service=oauth_http_service,
        refresh_enabled=False,
    )
