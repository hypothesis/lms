from unittest import mock

import pytest
from pyramid import httpexceptions

from lms.validation import ValidationError
from lms.views import error


class TestNotFound:
    def test_it_does_not_report_exception_to_sentry(self, pyramid_request, sentry_sdk):
        error.notfound(pyramid_request)

        sentry_sdk.capture_exception.assert_not_called()

    def test_it_sets_response_status(self, pyramid_request):
        error.notfound(pyramid_request)

        assert pyramid_request.response.status_int == 404

    def test_it_shows_a_generic_error_message_to_the_user(self, pyramid_request):
        result = error.notfound(pyramid_request)

        assert result["message"] == "Page not found"


class TestForbidden:
    def test_it_does_not_report_exception_to_sentry(self, pyramid_request, sentry_sdk):
        error.forbidden(pyramid_request)

        sentry_sdk.capture_exception.assert_not_called()

    def test_it_sets_response_status(self, pyramid_request):
        error.forbidden(pyramid_request)

        assert pyramid_request.response.status_int == 403

    def test_it_shows_a_generic_error_message_to_the_user(self, pyramid_request):
        result = error.forbidden(pyramid_request)

        assert result["message"] == "You're not authorized to view this page"


class TestHTTPClientError:
    def test_it_does_not_report_exception_to_sentry(self, pyramid_request, sentry_sdk):
        exc = httpexceptions.HTTPBadRequest()

        error.http_client_error(exc, pyramid_request)

        sentry_sdk.capture_exception.assert_not_called()

    def test_it_sets_response_status(self, pyramid_request):
        exc = httpexceptions.HTTPBadRequest()

        error.http_client_error(exc, pyramid_request)

        assert pyramid_request.response.status_int == 400

    def test_it_shows_the_exception_message_to_the_user(self, pyramid_request):
        exc = httpexceptions.HTTPBadRequest("This is the error message")

        result = error.http_client_error(exc, pyramid_request)

        assert result["message"] == "This is the error message"


class TestHTTPServerError:
    def test_it_reports_exception_to_sentry(self, pyramid_request, sentry_sdk):
        exc = httpexceptions.HTTPServerError()

        error.http_server_error(exc, pyramid_request)

        sentry_sdk.capture_exception.assert_called_once_with(exc)

    def test_it_sets_response_status(self, pyramid_request):
        exc = httpexceptions.HTTPServerError()

        error.http_server_error(exc, pyramid_request)

        assert pyramid_request.response.status_int == 500

    def test_it_shows_the_exception_message_to_the_user(self, pyramid_request):
        exc = httpexceptions.HTTPServerError("This is the error message")

        result = error.http_server_error(exc, pyramid_request)

        assert result["message"] == "This is the error message"


class TestValidationError:
    def test_it_sets_response_status(self, pyramid_request):
        exc = ValidationError(mock.sentinel.messages)

        error.validation_error(exc, pyramid_request)

        assert pyramid_request.response.status_int == 422

    def test_it_passes_the_exception_to_the_template(self, pyramid_request):
        exc = ValidationError(mock.sentinel.messages)

        template_data = error.validation_error(exc, pyramid_request)

        assert template_data["error"] == exc


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


@pytest.mark.usefixtures("pyramid_config")
class TestIncludeMe:
    def test_it_adds_the_exception_views(self, pyramid_config):
        error.includeme(pyramid_config)

        assert pyramid_config.add_exception_view.call_args_list == [
            mock.call(
                error.http_client_error,
                context=httpexceptions.HTTPClientError,
                renderer="lms:templates/error.html.jinja2",
            ),
            mock.call(
                error.http_server_error,
                context=httpexceptions.HTTPServerError,
                renderer="lms:templates/error.html.jinja2",
            ),
            mock.call(
                error.error,
                context=Exception,
                renderer="lms:templates/error.html.jinja2",
            ),
            mock.call(
                error.validation_error,
                context=ValidationError,
                renderer="lms:templates/validation_error.html.jinja2",
            ),
        ]

    @pytest.fixture
    def pyramid_config(self, pyramid_config):
        pyramid_config.add_exception_view = mock.MagicMock()
        return pyramid_config


@pytest.fixture(autouse=True)
def sentry_sdk(patch):
    return patch("lms.views.error.sentry_sdk")
