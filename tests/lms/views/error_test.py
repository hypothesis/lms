# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPNotImplemented
import pytest

from lms.views import error
from lms.exceptions import LTILaunchError


class TestHTTPError:
    def test_it_reports_exception_to_sentry(self, pyramid_request, sentry_sdk):
        exc = HTTPNotImplemented()

        error.http_error(exc, pyramid_request)

        sentry_sdk.capture_exception.assert_called_once_with(exc)

    def test_it_sets_response_status(self, pyramid_request):
        exc = HTTPNotImplemented()

        error.http_error(exc, pyramid_request)

        assert pyramid_request.response.status_int == 501

    def test_it_shows_the_exception_message_to_the_user(self, pyramid_request):
        exc = HTTPNotImplemented("This is the error message")

        result = error.http_error(exc, pyramid_request)

        assert result["message"] == "This is the error message"


class TestLTILaunchError:
    def test_it_reports_exception_to_sentry(self, pyramid_request, sentry_sdk):
        exc = LTILaunchError("the_message")

        error.lti_launch_error(exc, pyramid_request)

        sentry_sdk.capture_exception.assert_called_once_with(exc)

    def test_it_sets_response_status(self, pyramid_request):
        exc = LTILaunchError("the_message")

        error.lti_launch_error(exc, pyramid_request)

        assert pyramid_request.response.status_int == 400

    def test_it_shows_the_exception_message_to_the_user(self, pyramid_request):
        exc = LTILaunchError("the_message")

        result = error.lti_launch_error(exc, pyramid_request)

        assert result["message"] == "the_message"


class TestError:
    def test_it_does_not_report_exception_to_sentry(self, pyramid_request, sentry_sdk):
        error.error(pyramid_request)

        # Although I don't think it would do any harm (sentry_sdk seems smart
        # enough to not double report the exception to Sentry) we don't need to
        # call capture_exception() in the case of a non-HTTPError exception
        # because Sentry's Pyramid integration does it for us automatically.
        sentry_sdk.capture_exception.assert_not_called()

    def test_it_sets_response_status(self, pyramid_request):
        error.error(pyramid_request)

        assert pyramid_request.response.status_int == 500

    def test_it_shows_a_generic_error_message_to_the_user(self, pyramid_request):
        result = error.error(pyramid_request)

        assert (
            result["message"]
            == "Sorry, but something went wrong. The issue has been reported and we'll try to fix it."
        )


@pytest.fixture(autouse=True)
def sentry_sdk(patch):
    return patch("lms.views.error.sentry_sdk")
