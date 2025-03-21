import datetime
from unittest.mock import sentinel

import pytest

from lms.db import CouldNotAcquireLock
from lms.models.oauth2_token import Service
from lms.services.exceptions import (
    ConcurrentTokenRefreshError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.services.oauth_http import OAuthHTTPService, factory
from lms.validation import ValidationError
from tests import factories


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
        http_service.request.side_effect = ExternalRequestError

        with pytest.raises(ExternalRequestError):
            svc.request(sentinel.method, sentinel.url)

    def test_get_access_token(
        self,
        svc,
        call_get_access_token,
        http_service,
        OAuthTokenResponseSchema,
        oauth_token_response_schema,
        oauth2_token_service,
    ):
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
        validated_data = oauth_token_response_schema.parse.return_value
        oauth2_token_service.save.assert_called_once_with(
            validated_data["access_token"],
            validated_data["refresh_token"],
            validated_data["expires_in"],
            svc.service,
        )

    def test_get_access_token_if_theres_no_refresh_token_or_expires_in(
        self,
        svc,
        call_get_access_token,
        oauth_token_response_schema,
        oauth2_token_service,
    ):
        # refresh_token and expires_in are optional fields in
        # OAuthTokenResponseSchema so get_access_token() has to still work
        # if they're missing from the validated data.
        oauth_token_response_schema.parse.return_value = {
            "access_token": "access_token"
        }

        call_get_access_token()

        oauth2_token_service.save.assert_called_once_with(
            "access_token", None, None, svc.service
        )

    def test_get_access_token_raises_ExternalRequestError_if_the_HTTP_request_fails(
        self, call_get_access_token, http_service
    ):
        http_service.post.side_effect = ExternalRequestError

        with pytest.raises(ExternalRequestError):
            call_get_access_token()

    def test_get_access_token_raises_ValidationError_if_the_response_is_invalid(
        self, call_get_access_token, oauth_token_response_schema
    ):
        oauth_token_response_schema.parse.side_effect = ValidationError({})

        with pytest.raises(ValidationError):
            call_get_access_token()

    def test_refresh_access_token(
        self,
        svc,
        http_service,
        OAuthTokenResponseSchema,
        oauth_token_response_schema,
        oauth2_token_service,
    ):
        svc.refresh_access_token(
            sentinel.token_url, sentinel.redirect_uri, sentinel.auth
        )

        oauth2_token_service.get.assert_called_once_with(svc.service)
        http_service.post.assert_called_once_with(
            sentinel.token_url,
            data={
                "grant_type": "refresh_token",
                "redirect_uri": sentinel.redirect_uri,
                "refresh_token": oauth2_token_service.get.return_value.refresh_token,
            },
            auth=sentinel.auth,
        )
        OAuthTokenResponseSchema.assert_called_once_with(http_service.post.return_value)
        validated_data = oauth_token_response_schema.parse.return_value
        oauth2_token_service.save.assert_called_once_with(
            validated_data["access_token"],
            validated_data["refresh_token"],
            validated_data["expires_in"],
            svc.service,
        )

    def test_refresh_access_token_if_theres_no_refresh_token_or_expires_in(
        self, svc, oauth_token_response_schema, oauth2_token_service
    ):
        # refresh_token and expires_in are optional fields in
        # OAuthTokenResponseSchema so refresh_access_token() has to still work
        # if they're missing from the validated data.
        oauth_token_response_schema.parse.return_value = {
            "access_token": "access_token"
        }

        svc.refresh_access_token(
            sentinel.token_url, sentinel.redirect_uri, sentinel.auth
        )

        oauth2_token_service.save.assert_called_once_with(
            "access_token", None, None, svc.service
        )

    def test_refresh_access_token_raises_if_we_dont_have_a_refresh_token(
        self, svc, oauth2_token_service
    ):
        oauth2_token_service.get.side_effect = OAuth2TokenError

        with pytest.raises(OAuth2TokenError):
            svc.refresh_access_token(
                sentinel.token_url, sentinel.redirect_uri, sentinel.auth
            )

    def test_refresh_access_token_raises_ExternalRequestError_if_the_HTTP_request_fails(
        self, svc, http_service
    ):
        http_service.post.side_effect = ExternalRequestError

        with pytest.raises(ExternalRequestError):
            svc.refresh_access_token(
                sentinel.token_url, sentinel.redirect_uri, sentinel.auth
            )

    def test_refresh_access_token_raises_OAuth2TokenError_if_our_refresh_token_is_invalid(
        self, svc, http_service
    ):
        http_service.post.side_effect = ExternalRequestError(
            response=factories.requests.Response(json_data={"error": "invalid_grant"})
        )

        with pytest.raises(OAuth2TokenError):
            svc.refresh_access_token(
                sentinel.token_url, sentinel.redirect_uri, sentinel.auth
            )

    def test_refresh_access_token_raises_ExternalRequestError_if_theres_an_unknown_OAuth_error_message(
        self, svc, http_service
    ):
        http_service.post.side_effect = ExternalRequestError(
            response=factories.requests.Response(json_data={"error": "unknown_error"})
        )

        with pytest.raises(ExternalRequestError):
            svc.refresh_access_token(
                sentinel.token_url, sentinel.redirect_uri, sentinel.auth
            )

    def test_refresh_access_token_raises_ValidationError_if_the_response_is_invalid(
        self, svc, oauth_token_response_schema
    ):
        oauth_token_response_schema.parse.side_effect = ValidationError({})

        with pytest.raises(ValidationError):
            svc.refresh_access_token(
                sentinel.token_url, sentinel.redirect_uri, sentinel.auth
            )

    @pytest.mark.parametrize("prevent_concurrent_refreshes", (False, True))
    def test_refresh_access_token_acquires_refresh_lock(
        self, svc, oauth2_token_service, prevent_concurrent_refreshes
    ):
        svc.refresh_access_token(
            sentinel.token_url,
            sentinel.redirect_uri,
            sentinel.auth,
            prevent_concurrent_refreshes=prevent_concurrent_refreshes,
        )

        # We acquire the lock whether or not concurrent refreshes are allowed,
        # but only raise if not allowed.
        oauth2_token_service.try_lock_for_refresh.assert_called_once()

    def test_refresh_access_does_not_raise_if_concurrent_refreshes_allowed(
        self,
        svc,
        oauth2_token_service,
    ):
        oauth2_token_service.try_lock_for_refresh.side_effect = CouldNotAcquireLock()
        svc.refresh_access_token(
            sentinel.token_url,
            sentinel.redirect_uri,
            sentinel.auth,
            prevent_concurrent_refreshes=False,
        )

    def test_refresh_access_token_raises_if_concurrent_refreshes_prevented(
        self,
        svc,
        oauth2_token_service,
    ):
        oauth2_token_service.try_lock_for_refresh.side_effect = CouldNotAcquireLock()

        with pytest.raises(ConcurrentTokenRefreshError):
            svc.refresh_access_token(
                sentinel.token_url,
                sentinel.redirect_uri,
                sentinel.auth,
            )

    def test_refresh_token_skips_if_token_is_current(
        self,
        svc,
        oauth2_token_service,
        http_service,
    ):
        token = oauth2_token_service.get(Service.LMS)
        token.received_at = datetime.datetime.utcnow()  # noqa: DTZ003

        svc.refresh_access_token(
            sentinel.token_url, sentinel.redirect_uri, sentinel.auth
        )

        http_service.post.assert_not_called()

    # nb. We don't list every API service here, just two to ensure that all
    # methods pass the right `service` when reading/saving tokens from the DB.
    @pytest.fixture(params=[Service.LMS, Service.CANVAS_STUDIO])
    def svc(self, request, http_service, oauth2_token_service):
        return OAuthHTTPService(http_service, oauth2_token_service, request.param)

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

        OAuthHTTPService.assert_called_once_with(
            http_service, oauth2_token_service, Service.LMS
        )
        assert service == OAuthHTTPService.return_value

    def test_with_custom_service(
        self, http_service, oauth2_token_service, pyramid_request, OAuthHTTPService
    ):
        api_service = Service.CANVAS_STUDIO

        service = factory(sentinel.context, pyramid_request, api_service)

        OAuthHTTPService.assert_called_once_with(
            http_service, oauth2_token_service, api_service
        )
        assert service == OAuthHTTPService.return_value

    def test_with_custom_user_id(
        self,
        OAuthHTTPService,
        pyramid_request,
        http_service,
        oauth2_token_service_factory,
    ):
        service = factory(sentinel.context, pyramid_request, user_id="custom_user_id")
        oauth2_token_service_factory.assert_called_once_with(
            sentinel.context,
            pyramid_request,
            application_instance=None,
            user_id="custom_user_id",
        )
        OAuthHTTPService.assert_called_once_with(
            http_service, oauth2_token_service_factory.return_value, Service.LMS
        )
        assert service == OAuthHTTPService.return_value

    def test_with_custom_application_instance(
        self,
        OAuthHTTPService,
        pyramid_request,
        http_service,
        oauth2_token_service_factory,
    ):
        mock_ai = sentinel.application_instance
        service = factory(
            sentinel.context, pyramid_request, application_instance=mock_ai
        )
        oauth2_token_service_factory.assert_called_once_with(
            sentinel.context,
            pyramid_request,
            application_instance=mock_ai,
            user_id=None,
        )
        OAuthHTTPService.assert_called_once_with(
            http_service, oauth2_token_service_factory.return_value, Service.LMS
        )
        assert service == OAuthHTTPService.return_value

    @pytest.fixture
    def OAuthHTTPService(self, patch):
        return patch("lms.services.oauth_http.OAuthHTTPService")

    @pytest.fixture
    def oauth2_token_service_factory(self, patch):
        return patch("lms.services.oauth_http.oauth2_token_service_factory")


@pytest.fixture(autouse=True)
def OAuthTokenResponseSchema(patch):
    OAuthTokenResponseSchema = patch("lms.services.oauth_http.OAuthTokenResponseSchema")
    OAuthTokenResponseSchema.return_value.parse.return_value = {
        "access_token": "access_token",
        "refresh_token": "refresh_token",
        "expires_in": 1234,
    }
    return OAuthTokenResponseSchema


@pytest.fixture
def oauth_token_response_schema(OAuthTokenResponseSchema):
    return OAuthTokenResponseSchema.return_value
