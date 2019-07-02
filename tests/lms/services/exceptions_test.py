import json
from unittest import mock

import httpretty
import pytest
import requests

from lms.services import (
    CanvasAPIError,
    CanvasAPIAccessTokenError,
    CanvasAPIServerError,
    ExternalRequestError,
)
from lms.validation import ValidationError


class TestExternalRequestError:
    # If no ``response`` kwarg is given to ExternalRequestError() then
    # __str__() falls back on the HTTPInternalServerError base class's
    # __str__() which is to use the given detail message string as the string
    # representation of the exception.
    def test_when_theres_no_response_uses_detail_message_as_str(self):
        err = ExternalRequestError("Connecting to Hypothesis failed")

        assert str(err) == "Connecting to Hypothesis failed"

    # If a ``response`` arg is given to ExternalRequestError() then it uses the
    # Response object's attributes to format a more informative string
    # representation of the exception. Not all Response objects necessarily
    # have values for every attribute - certain attributes can be ``None`` or
    # the empty string, so ``__str__()`` needs to handle those.
    @pytest.mark.parametrize(
        "status_code,reason,text,expected",
        [
            (
                400,
                "Bad Request",
                "Name too long",
                "Connecting to Hypothesis failed: 400 Bad Request Name too long",
            ),
            (
                None,
                "Bad Request",
                "Name too long",
                "Connecting to Hypothesis failed: Bad Request Name too long",
            ),
            (
                400,
                None,
                "Name too long",
                "Connecting to Hypothesis failed: 400 Name too long",
            ),
            (
                400,
                "Bad Request",
                "",
                "Connecting to Hypothesis failed: 400 Bad Request",
            ),
        ],
    )
    def test_when_theres_a_response_it_uses_it_in_str(
        self, status_code, reason, text, expected
    ):
        response = mock.create_autospec(
            requests.Response,
            instance=True,
            status_code=status_code,
            reason=reason,
            text=text,
        )
        err = ExternalRequestError("Connecting to Hypothesis failed", response=response)

        assert str(err) == expected


class TestRaiseFrom:
    @pytest.mark.parametrize(
        "status,expected_status,expected_exception_class,expected_exception_string",
        [
            # A 401 Unauthorized response from Canvas, because our access token was
            # expired or deleted.
            (
                401,
                "401 Unauthorized",
                CanvasAPIAccessTokenError,
                "401 Client Error: Unauthorized for url: https://example.com/",
            ),
            # A 400 Bad Request response from Canvas, because we sent an invalid
            # parameter or something.
            (
                400,
                "400 Bad Request",
                CanvasAPIServerError,
                "400 Client Error: Bad Request for url: https://example.com/",
            ),
            # An unexpected error response from Canvas.
            (
                500,
                "500 Internal Server Error",
                CanvasAPIServerError,
                "500 Server Error: Internal Server Error for url: https://example.com/",
            ),
        ],
    )
    def test_it_raises_the_right_CanvasAPIError_subclass_for_different_Canvas_responses(
        self,
        status,
        expected_status,
        expected_exception_class,
        expected_exception_string,
    ):
        cause = self._requests_exception(status=status)

        with pytest.raises(
            expected_exception_class, match="Calling the Canvas API failed"
        ) as exc_info:
            CanvasAPIError.raise_from(cause)

        raised_exception = exc_info.value
        assert raised_exception.__cause__ == cause
        assert raised_exception.response == cause.response
        assert raised_exception.details == {
            "exception": expected_exception_string,
            "validation_errors": None,
            "response": {"status": expected_status, "body": '{"foo": "bar"}'},
        }

    @pytest.mark.parametrize(
        "cause,expected_exception_string",
        [
            (requests.RequestException(), "RequestException()"),
            (requests.ConnectionError(), "ConnectionError()"),
            (requests.TooManyRedirects(), "TooManyRedirects()"),
            (requests.ConnectTimeout(), "ConnectTimeout()"),
            (requests.ReadTimeout(), "ReadTimeout()"),
        ],
    )
    def test_it_raises_CanvasAPIServerError_for_all_other_requests_errors(
        self, cause, expected_exception_string
    ):
        with pytest.raises(
            CanvasAPIServerError, match="Calling the Canvas API failed"
        ) as exc_info:
            CanvasAPIError.raise_from(cause)

        raised_exception = exc_info.value
        assert raised_exception.__cause__ == cause
        # For these kinds of errors no response (either successful or
        # unsuccessful) was ever received from Canvas (for example: the network
        # request timed out) so there's nothing to set as the response
        # property.
        assert raised_exception.response is None
        assert raised_exception.details == {
            "exception": expected_exception_string,
            "response": None,
            "validation_errors": None,
        }

    def test_it_raises_CanvasAPIServerError_for_a_successful_but_invalid_response(
        self, canvas_api_invalid_response
    ):
        cause = ValidationError("The response was invalid.")
        cause.response = canvas_api_invalid_response

        with pytest.raises(
            CanvasAPIServerError, match="Calling the Canvas API failed"
        ) as exc_info:
            CanvasAPIError.raise_from(cause)

        raised_exception = exc_info.value
        assert raised_exception.__cause__ == cause
        assert raised_exception.response == canvas_api_invalid_response
        assert raised_exception.details == {
            "exception": "Unable to process the contained instructions",
            "response": {"body": "Invalid", "status": "200 OK"},
            "validation_errors": "The response was invalid.",
        }

    @pytest.fixture
    def canvas_api_invalid_response(self):
        """Return a successful (200 OK) response with an invalid body."""
        httpretty.register_uri(
            httpretty.GET, "https://example.com", priority=1, status=200, body="Invalid"
        )
        return requests.get("https://example.com")

    @staticmethod
    def _requests_exception(**kwargs):
        httpretty.register_uri(
            httpretty.GET,
            "https://example.com",
            priority=1,
            body=json.dumps({"foo": "bar"}),
            **kwargs
        )

        response = requests.get("https://example.com")

        try:
            response.raise_for_status()
        except requests.RequestException as err:
            return err

        assert False, "We should never get here"
