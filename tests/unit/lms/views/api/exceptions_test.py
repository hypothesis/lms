from unittest.mock import call

import pytest
import requests
from pyramid.httpexceptions import HTTPBadRequest

from lms.services import CanvasAPIPermissionError, ExternalRequestError
from lms.validation import ValidationError
from lms.views.api.exceptions import APIExceptionViews, strip_queryparams
from tests import factories


class TestSchemaValidationError:
    def test_it(self, pyramid_request, views):
        json_data = views.validation_error()

        assert pyramid_request.response.status_code == 422
        assert json_data == {
            "message": "Unable to process the contained instructions",
            "details": "foobar",
        }

    @pytest.fixture
    def context(self):
        return ValidationError(messages="foobar")


class TestOAuth2TokenError:
    def test_it(self, pyramid_request, views):
        json_data = views.oauth2_token_error()

        assert pyramid_request.response.status_code == 400
        assert json_data == {}


class TestExternalRequestError:
    def test_it(self, context, pyramid_request, views, report_exception, sentry_sdk):
        json_data = views.external_request_error()

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
        ]

        report_exception.assert_called_once_with()
        assert pyramid_request.response.status_code == 400
        assert json_data == {
            "message": context.message,
            "details": {
                "request": {
                    "method": context.method,
                    "url": "https://example.com/",  # The URL without query string.
                },
                "response": {
                    "status_code": context.status_code,
                    "reason": context.reason,
                },
            },
        }

    @pytest.mark.parametrize("message", [None, ""])
    def test_it_injects_a_default_error_message(self, context, message, views):
        context.message = message

        json_data = views.external_request_error()

        assert json_data["message"] == "External request failed"

    @pytest.fixture
    def context(self):
        return ExternalRequestError(
            message="test_message",
            request=requests.Request(
                "GET", "https://example.com?foo=bar", data="request_body"
            ).prepare(),
            response=factories.requests.Response(
                status_code=418, reason="I'm a teapot", raw="Body text"
            ),
        )


class TestNotFound:
    def test_it_sets_response_status(self, pyramid_request, views):
        views.notfound()

        assert pyramid_request.response.status_int == 404

    def test_it_shows_a_generic_error_message_to_the_user(self, views):
        result = views.notfound()

        assert result["message"] == "Endpoint not found."


class TestForbidden:
    def test_it_sets_response_status(self, pyramid_request, views):
        views.forbidden()

        assert pyramid_request.response.status_int == 403

    def test_it_shows_a_generic_error_message_to_the_user(self, views):
        result = views.forbidden()

        assert result["message"] == "You're not authorized to view this page."


class TestHTTPBadRequest:
    def test_it(self, pyramid_request, views):
        json_data = views.http_bad_request()

        assert pyramid_request.response.status_int == 400
        assert json_data == {"message": "test_message"}

    @pytest.fixture
    def context(self):
        return HTTPBadRequest("test_message")


class TestAPIError:
    def test_it_with_a_CanvasAPIPermissionError(self, pyramid_request, views):
        context = views.context = CanvasAPIPermissionError()

        json_data = views.api_error()

        assert pyramid_request.response.status_code == 400
        assert json_data == {"error_code": context.error_code}

    def test_it_with_an_unexpected_error(self, pyramid_request, views):
        views.context = RuntimeError("Totally unexpected")

        json_data = views.api_error()

        assert pyramid_request.response.status_code == 500
        assert json_data == {
            "message": (
                "A problem occurred while handling this request. Hypothesis has been"
                " notified."
            )
        }


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
