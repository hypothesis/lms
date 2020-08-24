from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPServerError

from lms.validation import ValidationError
from lms.views import exceptions


class ExceptionViewTest:
    view = None
    exception = None

    expected_result = None
    response_status = None
    report_to_sentry = None

    def handle(self, pyramid_request):
        if self.exception is None:
            return type(self).view(  # pylint:disable=not-callable
                mock.sentinel.exception, pyramid_request
            )

        return type(self).view(  # pylint:disable=not-callable
            self.exception, pyramid_request
        )

    def test_it_reports_exception_to_sentry_as_appropriate(
        self, pyramid_request, h_pyramid_sentry
    ):
        self.handle(pyramid_request)

        if self.report_to_sentry:
            h_pyramid_sentry.report_exception.assert_called_once()
        else:
            h_pyramid_sentry.report_exception.assert_not_called()

    def test_it_sets_response_status(self, pyramid_request):
        self.handle(pyramid_request)

        assert pyramid_request.response.status_int == self.response_status

    def test_it_produces_the_expected_template_vars(self, pyramid_request):
        result = self.handle(pyramid_request)

        assert result == self.expected_result


class TestNotFound(ExceptionViewTest):
    view = exceptions.notfound
    exception = None

    response_status = 404
    report_to_sentry = False
    expected_result = {"message": "Page not found"}


class TestForbidden(ExceptionViewTest):
    view = exceptions.forbidden
    exception = None

    response_status = 403
    report_to_sentry = False
    expected_result = {"message": "You're not authorized to view this page"}


class TestHTTPClientError(ExceptionViewTest):
    view = exceptions.http_client_error
    exception = HTTPBadRequest("This is the error message")

    response_status = 400
    report_to_sentry = False
    expected_result = {"message": exception.args[0]}


class TestHTTPServerError(ExceptionViewTest):
    view = exceptions.http_server_error
    exception = HTTPServerError("This is the error message")

    response_status = 500
    report_to_sentry = True
    expected_result = {"message": exception.args[0]}


class TestValidationError(ExceptionViewTest):
    view = exceptions.validation_error
    exception = ValidationError(mock.sentinel.messages)

    response_status = 422
    report_to_sentry = False
    expected_result = {"error": exception}


class TestError(ExceptionViewTest):
    view = exceptions.error
    exception = None

    response_status = 500
    # Although I don't think it would do any harm (sentry_sdk seems smart
    # enough to not double report the exception to Sentry) we don't need to
    # call report_exception() in the case of a non-HTTPError exception
    # because Sentry's Pyramid integration does it for us automatically.
    report_to_sentry = False
    expected_result = {
        "message": "Sorry, but something went wrong. The issue has been reported and we'll try to fix it."
    }


@pytest.fixture(autouse=True)
def h_pyramid_sentry(patch):
    return patch("lms.views.exceptions.h_pyramid_sentry")
