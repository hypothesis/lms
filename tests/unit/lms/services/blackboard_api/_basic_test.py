from unittest.mock import sentinel

import pytest

from lms.services.blackboard_api._basic import (
    BasicClient,
    BlackboardErrorResponseSchema,
)
from lms.services.exceptions import HTTPError, OAuth2TokenError
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
    def test_request(self, basic_client, oauth_http_service, path, expected_url):
        response = basic_client.request("GET", path)

        oauth_http_service.request.assert_called_once_with("GET", expected_url)
        assert response == oauth_http_service.request.return_value

    def test_request_raises_OAuth2TokenError_if_our_access_token_isnt_working(
        self, basic_client, oauth_http_service
    ):
        oauth_http_service.request.side_effect = HTTPError(
            factories.requests.Response(
                json_data={"status": 401, "message": "Bearer token is invalid"}
            )
        )

        with pytest.raises(OAuth2TokenError):
            basic_client.request("GET", "foo/bar/")

    def test_request_raises_HTTPError_if_the_HTTP_request_fails(
        self, basic_client, oauth_http_service
    ):
        oauth_http_service.request.side_effect = HTTPError(
            factories.requests.Response(
                # Just some unrecognized error response from Blackboard.
                json_data={"foo": "bar"}
            )
        )

        with pytest.raises(HTTPError):
            basic_client.request("GET", "foo/bar/")

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
