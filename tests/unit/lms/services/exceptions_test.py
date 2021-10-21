import json

import httpretty
import pytest
import requests

from lms.services import (
    CanvasAPIError,
    CanvasAPIPermissionError,
    CanvasAPIServerError,
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
        assert err.text == "Body text"

    def test_it_when_theres_no_response(self):
        err = ExternalRequestError()

        assert err.status_code is None
        assert err.reason is None
        assert err.text is None

    @pytest.mark.parametrize(
        "message,response,expected",
        [
            (
                None,
                None,
                "ExternalRequestError(message=None, response=Response(status_code=None, reason=None, text=None))",
            ),
            (
                "Connecting to Hypothesis failed",
                factories.requests.Response(
                    status_code=400,
                    reason="Bad Request",
                    raw="Name too long",
                ),
                "ExternalRequestError(message='Connecting to Hypothesis failed', response=Response(status_code=400, reason='Bad Request', text='Name too long'))",
            ),
        ],
    )
    def test_str(self, message, response, expected):
        assert str(ExternalRequestError(message=message, response=response)) == expected


class TestCanvasAPIError:
    @pytest.mark.parametrize(
        "status,body,expected_status,expected_exception_class",
        [
            # A 401 Unauthorized response from Canvas, because our access token was
            # expired or deleted.
            (
                401,
                json.dumps({"errors": [{"message": "Invalid access token."}]}),
                "401 Unauthorized",
                OAuth2TokenError,
            ),
            # A 401 Unauthorized response from Canvas, because our access token had
            # insufficient scopes;
            (
                401,
                json.dumps(
                    {"errors": [{"message": "Insufficient scopes on access token."}]}
                ),
                "401 Unauthorized",
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
                "400 Bad Request",
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
                "401 Unauthorized",
                CanvasAPIPermissionError,
            ),
            # A 400 Bad Request response from Canvas, because we sent an invalid
            # parameter or something.
            (
                400,
                json.dumps({"test": "body"}),
                "400 Bad Request",
                CanvasAPIServerError,
            ),
            # An unexpected error response from Canvas.
            (500, "test_body", "500 Internal Server Error", CanvasAPIServerError),
        ],
    )
    def test_it_raises_the_right_subclass_for_different_Canvas_responses(
        self, status, body, expected_status, expected_exception_class
    ):
        cause = self._requests_exception(status=status, body=body)

        raised_exception = self.assert_raises(cause, expected_exception_class)

        assert raised_exception.__cause__ == cause
        assert raised_exception.response == cause.response
        assert raised_exception.details == {
            "validation_errors": None,
            "response": {"status": expected_status, "body": body},
        }

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
        raised_exception = self.assert_raises(cause, CanvasAPIServerError)

        assert raised_exception.__cause__ == cause
        # For these kinds of errors no response (either successful or
        # unsuccessful) was ever received from Canvas (for example: the network
        # request timed out) so there's nothing to set as the response
        # property.
        assert raised_exception.response is None
        assert raised_exception.details == {
            "response": None,
            "validation_errors": None,
        }

    def test_it_raises_CanvasAPIServerError_for_a_successful_but_invalid_response(
        self, canvas_api_invalid_response
    ):
        cause = ValidationError("The response was invalid.")
        cause.response = canvas_api_invalid_response
        cause.response.body = "x" * 1000

        raised_exception = self.assert_raises(cause, CanvasAPIServerError)

        assert raised_exception.__cause__ == cause
        assert raised_exception.response == canvas_api_invalid_response
        assert raised_exception.details == {
            "response": {"body": "Invalid", "status": "200 OK"},
            "validation_errors": "The response was invalid.",
        }

    def test_it_truncates_the_body_if_it_is_very_long(self, canvas_api_long_response):
        # Make the response very long...
        cause = CanvasAPIServerError("The response was invalid.")
        cause.response = canvas_api_long_response

        raised_exception = self.assert_raises(cause, CanvasAPIServerError)

        body = raised_exception.details["response"]["body"]
        assert len(body) == 153
        assert body.endswith("...")

    def assert_raises(self, cause, expected_exception_class):
        with pytest.raises(
            expected_exception_class, match="Calling the Canvas API failed"
        ) as exc_info:
            CanvasAPIError.raise_from(cause)

        return exc_info.value

    @pytest.fixture
    def canvas_api_long_response(self):
        """Return a successful (200 OK) response with a long body."""
        httpretty.register_uri(
            httpretty.GET,
            "https://example.com",
            status=200,
            body="x" * 2000,
        )
        return requests.get("https://example.com")

    @pytest.fixture
    def canvas_api_invalid_response(self):
        """Return a successful (200 OK) response with an invalid body."""
        httpretty.register_uri(
            httpretty.GET, "https://example.com", status=200, body="Invalid"
        )
        return requests.get("https://example.com")

    @staticmethod
    def _requests_exception(**kwargs):  # pylint:disable=inconsistent-return-statements

        httpretty.register_uri(
            httpretty.GET,
            "https://example.com",
            body=kwargs.pop("body", json.dumps({"foo": "bar"})),
            **kwargs
        )

        response = requests.get("https://example.com")

        try:
            response.raise_for_status()
        except requests.RequestException as err:
            return err
