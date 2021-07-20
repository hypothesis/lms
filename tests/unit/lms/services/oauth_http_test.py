from unittest.mock import sentinel

import pytest

from lms.services.exceptions import HTTPError, OAuth2TokenError
from lms.services.oauth_http import OAuthHTTPService, factory


class TestOAuthHTTPService:
    def test_it(self, svc, http_service, oauth2_token_service):
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

    def test_it_crashes_if_theres_already_an_Authorization_header(self, svc):
        with pytest.raises(AssertionError):
            svc.request(sentinel.method, sentinel.url, headers={"Authorization": "foo"})

    def test_it_raises_if_theres_no_access_token_for_the_user(
        self, svc, oauth2_token_service
    ):
        oauth2_token_service.get.side_effect = OAuth2TokenError

        with pytest.raises(OAuth2TokenError):
            svc.request(sentinel.method, sentinel.url)

    def test_it_raises_if_the_HTTP_request_fails(self, svc, http_service):
        http_service.request.side_effect = HTTPError

        with pytest.raises(HTTPError):
            svc.request(sentinel.method, sentinel.url)

    @pytest.fixture
    def svc(self, http_service, oauth2_token_service):
        return OAuthHTTPService(http_service, oauth2_token_service)


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
