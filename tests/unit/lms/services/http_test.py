from unittest.mock import Mock, create_autospec, sentinel

import httpretty
import marshmallow
import pytest
import requests
from h_matchers import Any

from lms.services.exceptions import HTTPError, HTTPValidationError, OAuth2TokenError
from lms.services.http import HTTPService, factory
from lms.validation import RequestsResponseSchema, ValidationError


class TestHTTPService:
    @pytest.mark.parametrize("method", ["GET", "PUT", "POST", "PATCH", "DELETE"])
    def test_it_sends_the_request_and_returns_the_response(self, svc, method, url):
        httpretty.register_uri(method, url, body="test_response")

        response = svc.request(method, url)

        assert response.status_code == 200
        assert response.text == "test_response"
        assert httpretty.last_request() == Any.object.with_attrs(
            {"url": url, "method": method}
        )

    @pytest.mark.parametrize("method", ["GET", "PUT", "POST", "PATCH", "DELETE"])
    def test_convenience_methods(self, svc, url, method):
        httpretty.register_uri(method, url, body="test_response")

        getattr(svc, method.lower())(url)

        assert httpretty.last_request() == Any.object.with_attrs(
            {"url": url, "method": method}
        )

    def test_it_sends_request_params(self, svc, url):
        svc.request("GET", url, params={"test_param": "test_value"})

        assert httpretty.last_request() == Any.object.with_attrs(
            {"url": f"{url}?test_param=test_value"}
        )

    def test_it_sends_request_data(self, svc, url):
        svc.request("GET", url, data={"test_key": "test_value"})

        assert httpretty.last_request() == Any.object.with_attrs(
            {"body": b"test_key=test_value"}
        )

    def test_it_sends_request_json(self, svc, url):
        svc.request("GET", url, json={"test_key": "test_value"})

        assert httpretty.last_request() == Any.object.with_attrs(
            {"body": b'{"test_key": "test_value"}'}
        )

    def test_it_sends_request_headers(self, svc, url):
        svc.request("GET", url, headers={"HEADER_KEY": "HEADER_VALUE"})

        assert httpretty.last_request().headers["HEADER_KEY"] == "HEADER_VALUE"

    def test_it_sends_request_auth(self, svc, url):
        svc.request("GET", url, auth=("user", "pass"))

        assert httpretty.last_request().headers["Authorization"] == "Basic dXNlcjpwYXNz"

    def test_it_uses_custom_timeouts(self, session):
        svc = HTTPService(sentinel.oauth2_token_service, session)

        svc.request("GET", "https://example.com", timeout=3)

        assert session.request.call_args[1]["timeout"] == 3

    def test_it_passes_arbitrary_kwargs_to_requests(self, svc):
        session = Mock()
        svc = HTTPService(sentinel.oauth2_token_service, session)

        svc.request("GET", "https://example.com", foo="bar")

        assert session.request.call_args[1]["foo"] == "bar"

    @pytest.mark.parametrize(
        "exception",
        [
            requests.ConnectionError(),
            requests.HTTPError(),
            requests.ReadTimeout(),
            requests.TooManyRedirects(),
        ],
    )
    def test_it_raises_if_sending_the_request_fails(self, exception, session):
        session.request.side_effect = exception
        svc = HTTPService(sentinel.oauth2_token_service, session)

        with pytest.raises(HTTPError) as exc_info:
            svc.request("GET", "https://example.com")

        assert exc_info.value.response is None
        assert exc_info.value.__cause__ == exception

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 500])
    def test_it_raises_if_the_response_is_an_error(self, svc, url, status):
        httpretty.register_uri("GET", url, status=status)

        with pytest.raises(HTTPError) as exc_info:
            svc.request("GET", url)

        assert isinstance(exc_info.value.__cause__, requests.HTTPError)
        assert exc_info.value.response == Any.instance_of(requests.Response).with_attrs(
            {"status_code": status}
        )

    def test_if_a_schema_is_given_it_returns_the_validated_data(self, svc, url):
        response = svc.request("GET", url, schema=self.Schema)

        assert response.validated_data == {"test_response_key": "TEST_RESPONSE_VALUE"}

    def test_if_a_schema_is_given_it_raises_if_the_response_is_invalid(self, svc, url):
        httpretty.register_uri("GET", url, body="")

        with pytest.raises(HTTPValidationError) as exc_info:
            svc.request("GET", url, schema=self.Schema)

        assert isinstance(exc_info.value.__cause__, ValidationError)

    @pytest.mark.parametrize("method", ["GET", "PUT", "POST", "PATCH", "DELETE"])
    def test_if_oauth_is_True_it_adds_an_Authorization_header(
        self, svc, url, oauth2_token_service, method
    ):
        oauth2_token_service.get.return_value.access_token = "TEST_ACCESS_TOKEN"
        httpretty.register_uri(method, url)

        svc.request(method, url, oauth=True)

        request_headers = httpretty.last_request().headers
        assert request_headers.get("Authorization") == "Bearer TEST_ACCESS_TOKEN"

    def test_oauth_with_custom_header(self, svc, url, oauth2_token_service):
        # You can use oauth=True (which will inject an Authorization header) at
        # the same time as passing your own custom headers.
        oauth2_token_service.get.return_value.access_token = "TEST_ACCESS_TOKEN"

        svc.request("GET", url, oauth=True, headers={"foo": "FOO"})

        request_headers = httpretty.last_request().headers
        assert request_headers.get("Authorization") == "Bearer TEST_ACCESS_TOKEN"
        assert request_headers.get("foo") == "FOO"

    def test_oauth_raises_with_a_custom_Authorization_header(self, svc, url):
        # You can't use oauth=True at the same time as a custom Authorization
        # header.
        with pytest.raises(AssertionError):
            svc.request("GET", url, oauth=True, headers={"Authorization": "foo"})

    def test_oauth_raises_if_theres_no_access_token_for_the_user(
        self, svc, url, oauth2_token_service
    ):
        oauth2_token_service.get.side_effect = OAuth2TokenError

        with pytest.raises(OAuth2TokenError):
            svc.request("GET", url, oauth=True)

    class Schema(RequestsResponseSchema):
        test_response_key = marshmallow.fields.String(required=True)

        @marshmallow.post_load
        def post_load(self, data, **_kwargs):
            data["test_response_key"] = data["test_response_key"].upper()
            return data

    @pytest.fixture
    def url(self):
        """Return the URL that we'll be sending test requests to."""
        return "https://example.com/example"

    @pytest.fixture(autouse=True)
    def test_response(self, url):
        httpretty.register_uri(
            "GET", url, body='{"test_response_key": "test_response_value"}', priority=-1
        )

    @pytest.fixture
    def session(self):
        return create_autospec(requests.Session, instance=True, spec_set=True)

    @pytest.fixture
    def svc(self, oauth2_token_service):
        return HTTPService(oauth2_token_service)


@pytest.mark.usefixtures("oauth2_token_service")
class TestFactory:
    def test_it(self, pyramid_request):
        assert isinstance(factory(sentinel.context, pyramid_request), HTTPService)
