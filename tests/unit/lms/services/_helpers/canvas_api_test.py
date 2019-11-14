from unittest import mock

import pytest
from requests import ConnectionError, HTTPError, ReadTimeout, Request, TooManyRedirects

from lms.services._helpers.canvas_api import CanvasAPIHelper
from lms.services.exceptions import CanvasAPIError
from lms.validation import ValidationError
from lms.validation._helpers import PyramidRequestSchema


class TestCanvasAPIHelper:
    def test_access_token_request(self, ai_getter, helper, route_url):
        request = helper.access_token_request("test_authorization_code")

        ai_getter.developer_key.assert_called_once_with("test_consumer_key")
        ai_getter.developer_secret.assert_called_once_with("test_consumer_key")
        ai_getter.lms_url.assert_called_once_with("test_consumer_key")
        assert request.method == "POST"
        assert request.url == (
            "https://my-canvas-instance.com/login/oauth2/token"
            "?grant_type=authorization_code"
            "&client_id=test_developer_key"
            "&client_secret=test_developer_secret"
            "&redirect_uri=http%3A%2F%2Fexample.com%2Fcanvas_oauth_callback"
            "&code=test_authorization_code"
            "&replace_tokens=True"
        )

    def test_refresh_token_request(self, ai_getter, helper, route_url):
        request = helper.refresh_token_request("test_refresh_token")

        ai_getter.developer_key.assert_called_once_with("test_consumer_key")
        ai_getter.developer_secret.assert_called_once_with("test_consumer_key")
        ai_getter.lms_url.assert_called_once_with("test_consumer_key")
        assert request.method == "POST"
        assert request.url == (
            "https://my-canvas-instance.com/login/oauth2/token"
            "?grant_type=refresh_token"
            "&client_id=test_developer_key"
            "&client_secret=test_developer_secret"
            "&refresh_token=test_refresh_token"
        )

    def test_list_files_request(self, ai_getter, helper, route_url):
        request = helper.list_files_request("test_access_token", "test_course_id")

        ai_getter.lms_url.assert_called_once_with("test_consumer_key")
        assert request.method == "GET"
        assert request.headers["Authorization"] == "Bearer test_access_token"
        assert request.url == (
            "https://my-canvas-instance.com/api/v1/courses/test_course_id/files"
            "?content_types%5B%5D=application%2Fpdf"
            "&per_page=100"
        )

    def test_public_url_request(self, ai_getter, helper, route_url):
        request = helper.public_url_request("test_access_token", "test_file_id")

        ai_getter.lms_url.assert_called_once_with("test_consumer_key")
        assert request.method == "GET"
        assert request.headers["Authorization"] == "Bearer test_access_token"
        assert request.url == (
            "https://my-canvas-instance.com/api/v1/files/test_file_id/public_url"
        )

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("canvas_oauth_callback", "/canvas_oauth_callback")


class TestValidatedResponse:
    def test_it_sends_the_request(
        self, helper, prepared_request, requests, requests_session
    ):
        helper.validated_response(prepared_request)

        requests.Session.assert_called_once_with()
        requests_session.send.assert_called_once_with(prepared_request)

    def test_if_given_an_access_token_it_inserts_an_Authorization_header(
        self, helper, prepared_request, requests_session
    ):
        helper.validated_response(prepared_request, access_token="TEST_ACCESS_TOKEN")

        sent_request = requests_session.send.call_args[0][0]
        assert sent_request.headers["Authorization"] == "Bearer TEST_ACCESS_TOKEN"

    def test_if_given_an_access_token_it_replaces_an_existing_Authorization_header(
        self, helper, prepared_request, requests_session
    ):
        prepared_request.headers["Authorization"] = "Bearer OLD_ACCESS_TOKEN"
        helper.validated_response(prepared_request, access_token="NEW_ACCESS_TOKEN")

        sent_request = requests_session.send.call_args[0][0]
        assert sent_request.headers["Authorization"] == "Bearer NEW_ACCESS_TOKEN"

    @pytest.mark.parametrize(
        "exception", [ConnectionError(), HTTPError(), ReadTimeout(), TooManyRedirects()]
    )
    def test_it_raises_CanvasAPIError_if_the_request_fails(
        self, exception, helper, prepared_request, raise_from, requests_session
    ):
        requests_session.send.side_effect = exception

        with pytest.raises(CanvasAPIError, match="test_error_message") as exc_info:
            helper.validated_response(prepared_request)

        raise_from.assert_called_once_with(exception)

    def test_it_validates_the_response(
        self, helper, prepared_request, requests_response, Schema
    ):
        response = helper.validated_response(prepared_request, Schema)

        Schema.assert_called_once_with(requests_response)
        Schema.return_value.parse.assert_called_once_with()
        assert response.parsed_params == Schema.return_value.parse.return_value

    def test_it_raises_CanvasAPIError_if_the_response_is_invalid(
        self, helper, prepared_request, raise_from, Schema
    ):
        Schema.return_value.parse.side_effect = ValidationError("error message")

        with pytest.raises(CanvasAPIError, match="test_error_message") as exc_info:
            helper.validated_response(prepared_request, Schema)

        raise_from.assert_called_once_with(Schema.return_value.parse.side_effect)

    def test_it_skips_validation_if_no_schema_is_given(
        self, helper, prepared_request, Schema
    ):
        helper.validated_response(prepared_request)

        Schema.assert_not_called()

    @pytest.fixture
    def prepared_request(self):
        return Request("GET", "https://example.com").prepare()

    @pytest.fixture(autouse=True)
    def requests(self, patch):
        return patch("lms.services._helpers.canvas_api.requests")

    @pytest.fixture
    def requests_session(self, requests):
        """The requests.Session object."""
        return requests.Session.return_value

    @pytest.fixture(autouse=True)
    def requests_response(self, requests_session):
        """The requests.Response object returned by requests's send() method."""
        requests_response = requests_session.send.return_value
        requests_response.status_code = 200
        requests_response.reason = "OK"
        requests_response.text = ""
        return requests_response

    @pytest.fixture
    def Schema(self):
        return mock.create_autospec(PyramidRequestSchema, spec_set=True)


@pytest.fixture
def ai_getter(ai_getter):
    ai_getter.developer_key.return_value = "test_developer_key"
    ai_getter.developer_secret.return_value = "test_developer_secret"
    ai_getter.lms_url.return_value = "https://my-canvas-instance.com/"
    return ai_getter


@pytest.fixture
def helper(ai_getter, route_url):
    return CanvasAPIHelper("test_consumer_key", ai_getter, route_url)


@pytest.fixture(autouse=True)
def raise_from(request):
    # Always replace the original CanvasAPIError.raise_from() after each test.
    original = CanvasAPIError.raise_from

    def finalizer():
        CanvasAPIError.raise_from = original

    request.addfinalizer(finalizer)

    # Replace CanvasAPIError.raise_from() with a mock.
    # This is done manually because using the normal mock.patch() or even
    # mock.patch.object() to patch this static method didn't seem to work.
    CanvasAPIError.raise_from = mock.create_autospec(CanvasAPIError.raise_from)
    CanvasAPIError.raise_from.side_effect = CanvasAPIError("test_error_message")

    return CanvasAPIError.raise_from


@pytest.fixture
def route_url(pyramid_request):
    return pyramid_request.route_url
