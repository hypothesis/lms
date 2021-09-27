from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.models import ReusedConsumerKey
from lms.resources._js_config import JSConfig
from lms.services import HAPIError
from lms.validation import ValidationError
from lms.views import exceptions


class ExceptionViewTest:
    view = None
    exception = None

    expected_result = None
    response_status = None

    def handle(self, pyramid_request):
        if self.exception is None:
            return type(self).view(  # pylint:disable=not-callable
                mock.sentinel.exception, pyramid_request
            )

        return type(self).view(  # pylint:disable=not-callable
            self.exception, pyramid_request
        )

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
    expected_result = {"message": "Page not found"}


class TestForbidden(ExceptionViewTest):
    view = exceptions.forbidden
    exception = None

    response_status = 403
    expected_result = {"message": "You're not authorized to view this page"}


class TestHTTPClientError(ExceptionViewTest):
    view = exceptions.http_client_error
    exception = HTTPBadRequest("This is the error message")

    response_status = 400
    expected_result = {"message": exception.args[0]}


class TestHAPIError(ExceptionViewTest):
    view = exceptions.hapi_error
    exception = HAPIError("This is the error message")

    response_status = 500
    expected_result = {"message": "This is the error message"}


class TestValidationError(ExceptionViewTest):
    view = exceptions.validation_error
    exception = ValidationError(mock.sentinel.messages)

    response_status = 422
    expected_result = {"error": exception}


class TestError(ExceptionViewTest):
    view = exceptions.error
    exception = None

    response_status = 500
    expected_result = {
        "message": "Sorry, but something went wrong. The issue has been reported and we'll try to fix it."
    }


class TestReusedGuidErrorExceptionView:
    def test_application_reused_tool_guid(self, pyramid_request):
        exceptions.reused_tool_guid_error(
            ReusedConsumerKey("existing_guid", "new_guid"),
            pyramid_request,
        )

        js_config = pyramid_request.context.js_config
        js_config.enable_error_dialog_mode.assert_called_with(
            error_code=JSConfig.ErrorCode.REUSED_TOOL_GUID,
            error_details={
                "existing_tool_consumer_guid": "existing_guid",
                "new_tool_consumer_guid": "new_guid",
            },
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)
        js_config.ErrorCode = JSConfig.ErrorCode
        pyramid_request.context = mock.Mock(js_config=js_config)
        return pyramid_request
