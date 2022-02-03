import json
from unittest.mock import Mock, sentinel

import httpretty
import pytest
import requests

from lms.services import (
    CanvasAPIError,
    CanvasAPIPermissionError,
    CanvasAPIServerError,
    ExternalAsyncRequestError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.validation import ValidationError
from tests import factories


class TestExternalRequestError:
    def test_it(self):
        response = factories.requests.Response(
            status_code=418, reason="I'm a teapot", raw="Body text"
        )

        err = ExternalRequestError(response=response)

        assert err.status_code == 418
        assert err.reason == "I'm a teapot"
        assert err.response_body == "Body text"

    def test_it_when_theres_no_response(self):
        err = ExternalRequestError()

        assert err.status_code is None
        assert err.reason is None
        assert err.response_body is None

    @pytest.mark.parametrize(
        "message,request_,response,validation_errors,cause,expected",
        [
            (
                None,
                None,
                None,
                None,
                None,
                "ExternalRequestError(message=None, cause=None, request=Request(method=None, url=None, body=None), response=Response(status_code=None, reason=None, body=None), validation_errors=None)",
            ),
            (
                "Connecting to Hypothesis failed",
                requests.Request(
                    "GET", "https://example.com", data="request_body"
                ).prepare(),
                factories.requests.Response(
                    status_code=400,
                    reason="Bad Request",
                    raw="Name too long",
                ),
                {"foo": ["bar"]},
                KeyError("cause"),
                "ExternalRequestError(message='Connecting to Hypothesis failed', cause=KeyError('cause'), request=Request(method='GET', url='https://example.com/', body='request_body'), response=Response(status_code=400, reason='Bad Request', body='Name too long'), validation_errors={'foo': ['bar']})",
            ),
        ],
    )
    def test_str(self, message, request_, response, validation_errors, cause, expected):
        err = ExternalRequestError(
            message=message,
            request=request_,
            response=response,
            validation_errors=validation_errors,
        )
        err.__cause__ = cause

        assert str(err) == expected


class TestExternalAsyncRequestError:
    @pytest.mark.parametrize(
        "response,exception,expected",
        [
            (None, False, None),
            (Mock(request_info=Mock(url="response-url")), False, "response-url"),
            (None, True, "exception-URL"),
            (Mock(request_info=Mock(url="response-url")), False, "response-url"),
        ],
    )
    def test_url(self, response, exception, expected):
        class TestException(Exception):
            request_info = Mock(url="exception-URL")

        err = ExternalAsyncRequestError(response=response)
        err.__cause__ = TestException() if exception else None

        assert err.url == expected

    @pytest.mark.parametrize(
        "response,expected",
        [
            (None, None),
            (Mock(reason="OK"), "OK"),
        ],
    )
    def test_reason(self, response, expected):
        err = ExternalAsyncRequestError(response=response)

        assert err.reason == expected

    @pytest.mark.parametrize(
        "response,exception,expected",
        [
            (None, False, None),
            (Mock(request_info=Mock(method="response-GET")), False, "response-GET"),
            (None, True, "exception-GET"),
            (
                Mock(request_info=Mock(method="response-GET")),
                True,
                "response-GET",
            ),
        ],
    )
    def test_method(self, response, exception, expected):
        class TestException(Exception):
            request_info = Mock(method="exception-GET")

        err = ExternalAsyncRequestError(response=response)
        err.__cause__ = TestException() if exception else None

        assert err.method == expected

    @pytest.mark.parametrize(
        "response,expected",
        [
            (None, None),
            (Mock(status=200), 200),
        ],
    )
    def test_status_code(self, response, expected):
        err = ExternalAsyncRequestError(response=response)

        assert err.status_code == expected

    @pytest.mark.parametrize(
        "response,cause,expected",
        [
            (
                None,
                None,
                "ExternalAsyncRequestError(message=None, cause=None, request=Request(method=None, url=None, body=None), response=Response(status_code=None, reason=None, body=None), validation_errors=None)",
            ),
            (
                Mock(
                    status=400, reason="OK", request_info=Mock(method="POST", url="URL")
                ),
                KeyError("cause"),
                "ExternalAsyncRequestError(message=None, cause=KeyError('cause'), request=Request(method='POST', url='URL', body=None), response=Response(status_code=400, reason='OK', body=None), validation_errors=None)",
            ),
        ],
    )
    def test_str(self, response, cause, expected):
        err = ExternalAsyncRequestError(
            response=response,
        )
        err.__cause__ = cause

        assert str(err) == expected == repr(err)

    def test_response_body(self):
        assert not ExternalAsyncRequestError().response_body

    def test_request_body(self):
        assert not ExternalAsyncRequestError().request_body


class TestCanvasAPIError:
    @pytest.mark.parametrize(
        "status,body,expected_exception_class",
        [
            # A 401 Unauthorized response from Canvas, because our access token was
            # expired or deleted.
            (
                401,
                json.dumps({"errors": [{"message": "Invalid access token."}]}),
                OAuth2TokenError,
            ),
            # A 401 Unauthorized response from Canvas, because our access token had
            # insufficient scopes;
            (
                401,
                json.dumps(
                    {"errors": [{"message": "Insufficient scopes on access token."}]}
                ),
                OAuth2TokenError,
            ),
            # A 400 Bad Request response from Canvas, because our refresh token
            # was expired or deleted.
            (
                400,
                json.dumps(
                    {
                        "error": "invalid_request",
                        "error_description": "refresh_token not found",
                    }
                ),
                OAuth2TokenError,
            ),
            # A permissions error from Canvas, because the Canvas user doesn't
            # have permission to make the API call.
            (
                401,
                json.dumps(
                    {
                        "status": "unauthorized",
                        "errors": [
                            {"message": "user not authorized to perform that action"}
                        ],
                    }
                ),
                CanvasAPIPermissionError,
            ),
            # A 400 Bad Request response from Canvas, because we sent an invalid
            # parameter or something.
            (
                400,
                json.dumps({"test": "body"}),
                CanvasAPIServerError,
            ),
            # An unexpected error response from Canvas.
            (500, "test_body", CanvasAPIServerError),
        ],
    )
    def test_it_raises_the_right_subclass_for_different_Canvas_responses(
        self, status, body, expected_exception_class
    ):
        cause = requests.RequestException()
        response = factories.requests.Response(status_code=status, raw=body)

        raised_exception = self.assert_raises(cause, response, expected_exception_class)

        assert raised_exception.__cause__ == cause
        assert raised_exception.response == response
        assert raised_exception.validation_errors == sentinel.validation_errors

    @pytest.mark.parametrize(
        "cause",
        [
            requests.RequestException(),
            requests.ConnectionError(),
            requests.TooManyRedirects(),
            requests.ConnectTimeout(),
            requests.ReadTimeout(),
        ],
    )
    def test_it_raises_CanvasAPIServerError_for_all_other_requests_errors(self, cause):
        raised_exception = self.assert_raises(
            cause,
            # For these kinds of errors no response (either successful or
            # unsuccessful) was ever received from Canvas (for example: the
            # network request timed out) so there's nothing to set as the
            # response property.
            None,
            expected_exception_class=CanvasAPIServerError,
        )

        assert raised_exception.__cause__ == cause
        assert raised_exception.response is None

    def test_it_raises_CanvasAPIServerError_for_a_successful_but_invalid_response(
        self, canvas_api_invalid_response
    ):
        cause = ValidationError("The response was invalid.")

        raised_exception = self.assert_raises(
            cause,
            canvas_api_invalid_response,
            expected_exception_class=CanvasAPIServerError,
        )

        assert raised_exception.__cause__ == cause
        assert raised_exception.response == canvas_api_invalid_response

    def assert_raises(self, cause, response, expected_exception_class):
        with pytest.raises(
            expected_exception_class, match="Calling the Canvas API failed"
        ) as exc_info:
            CanvasAPIError.raise_from(
                cause,
                requests.Request(
                    "GET", "https://example.com", data="request_body"
                ).prepare(),
                response,
                validation_errors=sentinel.validation_errors,
            )

        return exc_info.value

    @pytest.fixture
    def canvas_api_invalid_response(self):
        """Return a successful (200 OK) response with an invalid body."""
        httpretty.register_uri(
            httpretty.GET, "https://example.com", status=200, body="Invalid"
        )
        canvas_api_invalid_response = requests.get("https://example.com")
        canvas_api_invalid_response.body = "x" * 1000
        return canvas_api_invalid_response
