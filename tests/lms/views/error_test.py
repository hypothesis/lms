# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPNotImplemented
import pytest

from lms.views.error import ErrorViews
from lms.exceptions import LTILaunchError


class TestErrorViews:
    def test_http_error_reports_exception_to_sentry(self, pyramid_request, sentry_sdk):
        exc = HTTPNotImplemented()

        ErrorViews(exc, pyramid_request).http_error()

        sentry_sdk.capture_exception.assert_called_once_with(exc)

    def test_http_error_sets_response_status(self, pyramid_request):
        exc = HTTPNotImplemented()

        ErrorViews(exc, pyramid_request).http_error()

        assert pyramid_request.response.status_int == 501

    def test_http_error_shows_the_exception_message_to_the_user(self, pyramid_request):
        exc = HTTPNotImplemented("This is the error message")

        result = ErrorViews(exc, pyramid_request).http_error()

        assert result["message"] == "This is the error message"

    def test_lti_launch_error_reports_exception_to_sentry(
        self, pyramid_request, sentry_sdk
    ):
        exc = LTILaunchError("the_message")

        ErrorViews(exc, pyramid_request).lti_launch_error()

        sentry_sdk.capture_exception.assert_called_once_with(exc)

    def test_lti_launch_error_sets_response_status(self, pyramid_request):
        exc = LTILaunchError("the_message")

        ErrorViews(exc, pyramid_request).lti_launch_error()

        assert pyramid_request.response.status_int == 400

    def test_lti_launch_error_shows_the_exception_message_to_the_user(
        self, pyramid_request
    ):
        exc = LTILaunchError("the_message")

        result = ErrorViews(exc, pyramid_request).http_error()

        assert result["message"] == "the_message"

    def test_error_does_not_report_exception_to_sentry(
        self, pyramid_request, sentry_sdk
    ):
        exc = RuntimeError()

        ErrorViews(exc, pyramid_request).error()

        # Although I don't think it would do any harm (sentry_sdk seems smart
        # enough to not double report the exception to Sentry) we don't need to
        # call capture_exception() in the case of a non-HTTPError exception
        # because Sentry's Pyramid integration does it for us automatically.
        sentry_sdk.capture_exception.assert_not_called()

    def test_error_sets_response_status(self, pyramid_request):
        exc = RuntimeError()

        ErrorViews(exc, pyramid_request).error()

        assert pyramid_request.response.status_int == 500

    def test_error_shows_a_generic_error_message_to_the_user(self, pyramid_request):
        exc = RuntimeError("the_specific_error_message")

        result = ErrorViews(exc, pyramid_request).error()

        assert (
            result["message"]
            == "Sorry, but something went wrong. The issue has been reported and we'll try to fix it."
        )

    @pytest.fixture(autouse=True)
    def sentry_sdk(self, patch):
        return patch("lms.views.error.sentry_sdk")
