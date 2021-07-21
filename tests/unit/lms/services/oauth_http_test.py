from unittest.mock import sentinel

import pytest

from lms.services.exceptions import HTTPError, OAuth2TokenError
from lms.services.oauth_http import OAuthHTTPService, factory
from lms.validation import ValidationError


class TestOAuthHTTPService:
    def test_request(self, svc, http_service, oauth2_token_service):
        response = svc.request(sentinel.method, sentinel.url, headers={"Foo": "bar"})

        http_service.request.assert_called_once_with(
            sentinel.method,
            sentinel.url,
            headers={
                "Authorization": f"Bearer {oauth2_token_service.get.return_value.access_token}",
                "Foo": "bar",
            },
        )
        assert response == http_service.request.return_value

    @pytest.mark.parametrize("method", ["GET", "PUT", "POST", "PATCH", "DELETE"])
    def test_convenience_methods(self, method, svc, http_service, oauth2_token_service):
        service_method = getattr(svc, method.lower())

        response = service_method(sentinel.url, headers={"Foo": "bar"})

        http_service.request.assert_called_once_with(
            method,
            sentinel.url,
            headers={
                "Authorization": f"Bearer {oauth2_token_service.get.return_value.access_token}",
                "Foo": "bar",
            },
        )
        assert response == http_service.request.return_value

    def test_request_crashes_if_theres_already_an_Authorization_header(self, svc):
        with pytest.raises(AssertionError):
            svc.request(sentinel.method, sentinel.url, headers={"Authorization": "foo"})

    def test_request_raises_if_theres_no_access_token_for_the_user(
        self, svc, oauth2_token_service
    ):
        oauth2_token_service.get.side_effect = OAuth2TokenError

        with pytest.raises(OAuth2TokenError):
            svc.request(sentinel.method, sentinel.url)

    def test_request_raises_if_the_HTTP_request_fails(self, svc, http_service):
        http_service.request.side_effect = HTTPError

        with pytest.raises(HTTPError):
            svc.request(sentinel.method, sentinel.url)

    def test_get_access_token(
        self,
        call_get_access_token,
        http_service,
        OAuthTokenResponseSchema,
        oauth_token_response_schema,
        oauth2_token_service,
    ):
        validated_data = oauth_token_response_schema.parse.return_value = {
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "expires_in": 1234,
        }

        call_get_access_token()

        http_service.post.assert_called_once_with(
            sentinel.token_url,
            data={
                "grant_type": "authorization_code",
                "redirect_uri": sentinel.redirect_uri,
                "code": sentinel.authorization_code,
            },
            auth=sentinel.auth,
        )
        OAuthTokenResponseSchema.assert_called_once_with(http_service.post.return_value)
        oauth2_token_service.save.assert_called_once_with(
            validated_data["access_token"],
            validated_data["refresh_token"],
            validated_data["expires_in"],
        )

    def test_get_access_token_if_theres_no_refresh_token_or_expires_in(
        self, call_get_access_token, oauth_token_response_schema, oauth2_token_service
    ):
        # refresh_token and expires_in are optional fields in
        # OAuthTokenResponseSchema so get_access_token() has to still work
        # if they're missing from the validated data.
        oauth_token_response_schema.parse.return_value = {
            "access_token": "access_token"
        }

        call_get_access_token()

        oauth2_token_service.save.assert_called_once_with("access_token", None, None)

    def test_get_access_token_raises_HTTPError_if_the_HTTP_request_fails(
        self, call_get_access_token, http_service
    ):
        http_service.post.side_effect = HTTPError

        with pytest.raises(HTTPError):
            call_get_access_token()

    def test_get_access_token_raises_ValidationError_if_the_response_is_invalid(
        self, call_get_access_token, oauth_token_response_schema
    ):
        oauth_token_response_schema.parse.side_effect = ValidationError({})

        with pytest.raises(ValidationError):
            call_get_access_token()

    @pytest.fixture
    def svc(self, http_service, oauth2_token_service):
        return OAuthHTTPService(http_service, oauth2_token_service)

    @pytest.fixture
    def call_get_access_token(self, svc):
        def call_get_access_token():
            svc.get_access_token(
                sentinel.token_url,
                sentinel.redirect_uri,
                sentinel.auth,
                sentinel.authorization_code,
            )

        return call_get_access_token


class TestFactory:
    def test_it(
        self, http_service, oauth2_token_service, pyramid_request, OAuthHTTPService
    ):
        service = factory(sentinel.context, pyramid_request)

        OAuthHTTPService.assert_called_once_with(http_service, oauth2_token_service)
        assert service == OAuthHTTPService.return_value

    @pytest.fixture
    def OAuthHTTPService(self, patch):
        return patch("lms.services.oauth_http.OAuthHTTPService")


@pytest.fixture(autouse=True)
def OAuthTokenResponseSchema(patch):
    return patch("lms.services.oauth_http.OAuthTokenResponseSchema")


@pytest.fixture
def oauth_token_response_schema(OAuthTokenResponseSchema):
    return OAuthTokenResponseSchema.return_value
