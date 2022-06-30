from unittest.mock import Mock, call, sentinel

import pytest
import requests
from pyramid.httpexceptions import HTTPBadRequest

from lms.services import (
    CanvasAPIPermissionError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.validation import ValidationError
from lms.views.api.exceptions import APIExceptionViews, ErrorBody, strip_queryparams
from tests import factories

pytestmark = pytest.mark.usefixtures("oauth2_token_service")


class TestSchemaValidationError:
    def test_it(self, pyramid_request, views):
        error_body = views.validation_error()

        assert pyramid_request.response.status_code == 422
        assert error_body == ErrorBody(
            message="Unable to process the contained instructions",
            details="foobar",
        )

    @pytest.fixture
    def context(self):
        return ValidationError(messages="foobar")


class TestOAuth2TokenError:
    def test_it(self, pyramid_request, views):
        error_body = views.oauth2_token_error()

        assert pyramid_request.response.status_code == 400
        assert error_body == ErrorBody()


class TestExternalRequestError:
    def test_it(self, context, pyramid_request, views, report_exception, sentry_sdk):
        error_body = views.external_request_error()

        assert sentry_sdk.set_context.call_args_list == [
            call(
                "request",
                {
                    "method": context.method,
                    "url": context.url,
                    "body": context.request_body,
                },
            ),
            call(
                "response",
                {
                    "status_code": context.status_code,
                    "reason": context.reason,
                    "body": context.response_body,
                },
            ),
            call("validation_errors", context.validation_errors),
        ]

        report_exception.assert_called_once_with()
        assert pyramid_request.response.status_code == 400
        assert error_body == ErrorBody(
            message=context.message,
            details={
                "request": {
                    "method": context.method,
                    "url": "https://example.com/",  # The URL without query string.
                },
                "response": {
                    "status_code": context.status_code,
                    "reason": context.reason,
                },
                "validation_errors": context.validation_errors,
            },
        )

    @pytest.mark.parametrize("message", [None, ""])
    def test_it_injects_a_default_error_message(self, context, message, views):
        context.message = message

        error_body = views.external_request_error()

        assert error_body.message == "External request failed"

    @pytest.fixture
    def context(self):
        context = ExternalRequestError(
            message="test_message",
            request=requests.Request(
                "GET", "https://example.com?foo=bar", data="request_body"
            ).prepare(),
            response=factories.requests.Response(
                status_code=418, reason="I'm a teapot", raw="Body text"
            ),
            validation_errors=sentinel.validation_errors,
        )
        context.__cause__ = ValueError("foo")
        return context


class TestNotFound:
    def test_it_sets_response_status(self, pyramid_request, views):
        views.notfound()

        assert pyramid_request.response.status_int == 404

    def test_it_shows_a_generic_error_message_to_the_user(self, views):
        result = views.notfound()

        assert result.message == "Endpoint not found."


class TestForbidden:
    def test_it_sets_response_status(self, pyramid_request, views):
        views.forbidden()

        assert pyramid_request.response.status_int == 403

    def test_it_shows_a_generic_error_message_to_the_user(self, views):
        result = views.forbidden()

        assert result.message == "You're not authorized to view this page."


class TestHTTPBadRequest:
    def test_it(self, pyramid_request, views):
        error_body = views.http_bad_request()

        assert pyramid_request.response.status_int == 400
        assert error_body == ErrorBody(message="test_message")

    @pytest.fixture
    def context(self):
        return HTTPBadRequest("test_message")


class TestAPIError:
    def test_it_with_a_CanvasAPIPermissionError(self, pyramid_request, views):
        context = views.context = CanvasAPIPermissionError()

        error_body = views.api_error()

        assert pyramid_request.response.status_code == 400
        assert error_body == ErrorBody(error_code=context.error_code)

    def test_it_with_an_unexpected_error(self, pyramid_request, views):
        views.context = RuntimeError("Totally unexpected")

        error_body = views.api_error()

        assert pyramid_request.response.status_code == 500
        assert error_body == ErrorBody(
            message=(
                "A problem occurred while handling this request. Hypothesis has been"
                " notified."
            )
        )


class TestErrorBody:
    @pytest.mark.parametrize(
        "error_body,expected",
        [
            (
                ErrorBody(),
                {},
            ),
            (
                ErrorBody(error_code=sentinel.error_code),
                {"error_code": sentinel.error_code},
            ),
            (
                ErrorBody(message=sentinel.message),
                {"message": sentinel.message},
            ),
            (
                ErrorBody(details=sentinel.details),
                {"details": sentinel.details},
            ),
            (
                ErrorBody(
                    error_code=sentinel.error_code,
                    message=sentinel.message,
                    details=sentinel.details,
                ),
                {
                    "error_code": sentinel.error_code,
                    "message": sentinel.message,
                    "details": sentinel.details,
                },
            ),
        ],
    )
    def test_json(self, pyramid_request, error_body, expected):
        assert error_body.__json__(pyramid_request) == expected

    @pytest.mark.usefixtures("with_refreshable_exception", "with_canvas")
    def test_json_includes_refresh_info_if_the_exception_is_refreshable(
        self, pyramid_request
    ):
        body = ErrorBody().__json__(pyramid_request)

        assert body["refresh"] == {
            "method": "POST",
            "path": pyramid_request.route_path("canvas_api.oauth.refresh"),
        }

    @pytest.mark.usefixtures("with_refreshable_exception", "with_blackboard")
    def test_json_includes_Blackboard_refresh_info_for_Blackboard_APIs(
        self, pyramid_request
    ):
        body = ErrorBody().__json__(pyramid_request)

        assert body["refresh"] == {
            "method": "POST",
            "path": pyramid_request.route_path("blackboard_api.oauth.refresh"),
        }

    @pytest.mark.usefixtures("with_refreshable_exception")
    def test_json_raises_if_unknown_product(self, pyramid_request):
        with pytest.raises(ValueError):
            ErrorBody().__json__(pyramid_request)

    @pytest.mark.usefixtures("with_refreshable_exception")
    def test_json_doesnt_include_refresh_info_if_we_dont_have_an_access_token(
        self, pyramid_request, oauth2_token_service
    ):
        oauth2_token_service.get.side_effect = OAuth2TokenError

        body = ErrorBody().__json__(pyramid_request)

        assert "refresh" not in body

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # When Pyramid calls an exception view it sets request.exception to the
        # exception that was raised by the original view:
        # https://docs.pylonsproject.org/projects/pyramid/en/latest/api/request.html#pyramid.request.Request.exception
        pyramid_request.exception = ValueError()

        pyramid_request.matched_route = Mock(spec_set=["name"])

        return pyramid_request

    @pytest.fixture
    def with_refreshable_exception(self, pyramid_request):
        pyramid_request.exception.refreshable = True


class TestStripQueryParams:
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://example.com/", "https://example.com/"),
            ("https://example.com/?foo=bar", "https://example.com/"),
            (None, None),
        ],
    )
    def test_it(self, url, expected):
        assert strip_queryparams(url) == expected


@pytest.fixture
def context():
    return None


@pytest.fixture
def views(context, pyramid_request):
    return APIExceptionViews(context, pyramid_request)


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("lms.views.api.exceptions.report_exception")


@pytest.fixture(autouse=True)
def sentry_sdk(patch):
    return patch("lms.views.api.exceptions.sentry_sdk")
