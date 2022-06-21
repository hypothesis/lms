from unittest.mock import sentinel

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


class TestBasicClient:
    def test_get_token(self, basic_client, oauth_http_service):
        basic_client.get_token(sentinel.authorization_code)

        oauth_http_service.get_access_token.assert_called_once_with(
            token_url="https://blackboard.example.com/learn/api/public/v1/oauth2/token",
            redirect_uri=sentinel.redirect_uri,
            auth=(sentinel.client_id, sentinel.client_secret),
            authorization_code=sentinel.authorization_code,
        )

    def test_refresh_access_token(self, basic_client, oauth_http_service):
        basic_client.refresh_access_token()

        oauth_http_service.refresh_access_token.assert_called_once_with(
            "https://blackboard.example.com/learn/api/public/v1/oauth2/token",
            sentinel.redirect_uri,
            auth=(sentinel.client_id, sentinel.client_secret),
        )

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
    def test_request_sends_the_request_and_returns_the_response(
        self, basic_client, oauth_http_service, path, expected_url
    ):
        response = basic_client.request("GET", path)

        oauth_http_service.request.assert_called_once_with("GET", expected_url)
        assert response == oauth_http_service.request.return_value

    def test_request_401s_from_Blackboard_are_refreshable(
        self, basic_client, oauth_http_service
    ):
        oauth_http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=401)
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            basic_client.request("GET", "/foo")

        assert exc_info.value.refreshable

    def test_request_raises_OAuth2TokenError_if_the_request_fails_with_an_access_token_error(
        self, basic_client, oauth_http_service
    ):
        oauth_http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(
                status_code=401, json_data={"message": "Bearer token is invalid"}
            )
        )

        with pytest.raises(OAuth2TokenError) as exc_info:
            basic_client.request("GET", "/foo")

        assert exc_info.value.refreshable

    def test_request_raises_ExternalRequestError_if_the_request_fails(
        self, basic_client, oauth_http_service
    ):
        oauth_http_service.request.side_effect = ExternalRequestError

        with pytest.raises(ExternalRequestError) as exc_info:
            basic_client.request("GET", "/foo")

        assert not exc_info.value.refreshable

    @pytest.fixture
    def basic_client(self, http_service, oauth_http_service):
        return BasicClient(
            blackboard_host="blackboard.example.com",
            client_id=sentinel.client_id,
            client_secret=sentinel.client_secret,
            redirect_uri=sentinel.redirect_uri,
            http_service=http_service,
            oauth_http_service=oauth_http_service,
        )
