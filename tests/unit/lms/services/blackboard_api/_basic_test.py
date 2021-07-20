from unittest.mock import sentinel

import pytest

from lms.services.blackboard_api._basic import (
    BasicClient,
    BlackboardErrorResponseSchema,
)
from lms.services.exceptions import HTTPError, OAuth2TokenError
from lms.validation import ValidationError
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
    def test_get_token(
        self,
        basic_client,
        http_service,
        oauth2_token_service,
        OAuthTokenResponseSchema,
        oauth_token_response_schema,
    ):
        oauth_token_response_schema.parse.return_value = {
            "access_token": sentinel.access_token,
            "refresh_token": sentinel.refresh_token,
            "expires_in": sentinel.expires_in,
        }

        basic_client.get_token(authorization_code=sentinel.authorization_code)

        # It calls the Blackboard API to get the access token.
        http_service.post.assert_called_once_with(
            "https://blackboard.example.com/learn/api/public/v1/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "redirect_uri": sentinel.redirect_uri,
                "code": sentinel.authorization_code,
            },
            auth=(sentinel.client_id, sentinel.client_secret),
        )

        # It validates the response.
        OAuthTokenResponseSchema.assert_called_once_with(http_service.post.return_value)

        # It saves the access token in the DB.
        oauth2_token_service.save.assert_called_once_with(
            sentinel.access_token, sentinel.refresh_token, sentinel.expires_in
        )

    def test_get_token_with_refresh_token(
        self,
        basic_client,
        http_service,
        oauth2_token_service,
        OAuthTokenResponseSchema,
        oauth_token_response_schema,
    ):
        oauth_token_response_schema.parse.return_value = {
            "access_token": sentinel.access_token,
            "refresh_token": sentinel.refresh_token,
            "expires_in": sentinel.expires_in,
        }

        basic_client.get_token(refresh_token=sentinel.refresh_token)

        # It calls the Blackboard API to get the access token.
        http_service.post.assert_called_once_with(
            "https://blackboard.example.com/learn/api/public/v1/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "redirect_uri": sentinel.redirect_uri,
                "refresh_token": sentinel.refresh_token,
            },
            auth=(sentinel.client_id, sentinel.client_secret),
        )

        # It validates the response.
        OAuthTokenResponseSchema.assert_called_once_with(http_service.post.return_value)

        # It saves the access token in the DB.
        oauth2_token_service.save.assert_called_once_with(
            sentinel.access_token, sentinel.refresh_token, sentinel.expires_in
        )

    def test_it_crashes_if_neither_authorization_code_nor_refresh_token_is_given(
        self, basic_client
    ):
        with pytest.raises(AssertionError):
            basic_client.get_token()

    def test_get_token_raises_HTTPError_if_the_HTTP_request_fails(
        self, basic_client, http_service
    ):
        http_service.post.side_effect = HTTPError

        with pytest.raises(HTTPError):
            basic_client.get_token(authorization_code=sentinel.authorization_code)

    def test_get_token_raises_ValidationError_if_Blackboards_response_is_invalid(
        self, basic_client, oauth_token_response_schema
    ):
        oauth_token_response_schema.parse.side_effect = ValidationError({})

        with pytest.raises(ValidationError):
            basic_client.get_token(authorization_code=sentinel.authorization_code)

    def test_get_token_if_theres_no_refresh_token_or_expires_in(
        self, basic_client, oauth2_token_service, oauth_token_response_schema
    ):
        # refresh_token and expires_in are optional fields in
        # OAuthTokenResponseSchema so get_token() has to still work if they're
        # missing from the validated data.
        oauth_token_response_schema.parse.return_value = {
            "access_token": sentinel.access_token
        }

        basic_client.get_token(authorization_code=sentinel.authorization_code)

        oauth2_token_service.save.assert_called_once_with(
            sentinel.access_token, None, None
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
    def test_request(self, basic_client, http_service, path, expected_url):
        response = basic_client.request("GET", path)

        http_service.request.assert_called_once_with("GET", expected_url, oauth=True)
        assert response == http_service.request.return_value

    def test_request_raises_OAuth2TokenError_if_our_access_token_isnt_working(
        self, basic_client, http_service
    ):
        http_service.request.side_effect = HTTPError(
            factories.requests.Response(
                json_data={"status": 401, "message": "Bearer token is invalid"}
            )
        )

        with pytest.raises(OAuth2TokenError):
            basic_client.request("GET", "foo/bar/")

    def test_request_raises_HTTPError_if_the_HTTP_request_fails(
        self, basic_client, http_service
    ):
        http_service.request.side_effect = HTTPError(
            factories.requests.Response(
                # Just some unrecognized error response from Blackboard.
                json_data={"foo": "bar"}
            )
        )

        with pytest.raises(HTTPError):
            basic_client.request("GET", "foo/bar/")

    @pytest.fixture
    def basic_client(self, http_service, oauth2_token_service):
        return BasicClient(
            blackboard_host="blackboard.example.com",
            client_id=sentinel.client_id,
            client_secret=sentinel.client_secret,
            redirect_uri=sentinel.redirect_uri,
            http_service=http_service,
            oauth2_token_service=oauth2_token_service,
        )


@pytest.fixture(autouse=True)
def OAuthTokenResponseSchema(patch):
    return patch("lms.services.blackboard_api._basic.OAuthTokenResponseSchema")


@pytest.fixture
def oauth_token_response_schema(OAuthTokenResponseSchema):
    return OAuthTokenResponseSchema.return_value
