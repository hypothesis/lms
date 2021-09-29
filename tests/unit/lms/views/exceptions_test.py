from unittest.mock import create_autospec, sentinel

import pytest
from pyramid import httpexceptions

from lms.models import ReusedConsumerKey
from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.services import HAPIError
from lms.validation import ValidationError
from lms.views.exceptions import ExceptionViews


class TestExceptionViews:
    def test_notfound(self, assert_response, pyramid_request):
        exception = httpexceptions.HTTPNotFound()

        template_data = ExceptionViews(exception, pyramid_request).notfound()

        assert_response(template_data, 404, message="Page not found")

    def test_forbidden(self, assert_response, pyramid_request):
        exception = httpexceptions.HTTPForbidden()

        template_data = ExceptionViews(exception, pyramid_request).forbidden()

        assert_response(
            template_data, 403, message="You're not authorized to view this page"
        )

    def test_http_client_error(self, assert_response, pyramid_request):
        exception = httpexceptions.HTTPBadRequest("http_client_error_test_explanation")

        template_data = ExceptionViews(exception, pyramid_request).http_client_error()

        assert_response(
            template_data,
            status=exception.status_int,
            message="http_client_error_test_explanation",
        )

    def test_hapi_error(self, assert_response, pyramid_request):
        exception = HAPIError("hapi_error_test_explanation")

        template_data = ExceptionViews(exception, pyramid_request).hapi_error()

        assert_response(template_data, 500, message="hapi_error_test_explanation")

    def test_validation_error(self, assert_response, pyramid_request):
        exception = ValidationError(sentinel.messages)

        template_data = ExceptionViews(exception, pyramid_request).validation_error()

        assert_response(template_data, status=exception.status_int, error=exception)

    def test_error(self, assert_response, pyramid_request):
        exception = RuntimeError()

        template_data = ExceptionViews(exception, pyramid_request).error()

        assert_response(
            template_data,
            500,
            message="Sorry, but something went wrong. The issue has been "
            "reported and we'll try to fix it.",
        )

    def test_reused_consumer_key(self, assert_response, pyramid_request):
        pyramid_request.context = create_autospec(
            LTILaunchResource,
            instance=True,
            spec_set=True,
            js_config=create_autospec(
                JSConfig,
                instance=True,
                spec_set=True,
                ErrorCode=JSConfig.ErrorCode,
            ),
        )
        exception = ReusedConsumerKey(sentinel.existing_guid, sentinel.new_guid)

        template_data = ExceptionViews(exception, pyramid_request).reused_consumer_key()

        assert_response(template_data, 400)
        pyramid_request.context.js_config.enable_error_dialog_mode.assert_called_with(
            error_code=JSConfig.ErrorCode.REUSED_CONSUMER_KEY,
            error_details={
                "existing_tool_consumer_instance_guid": sentinel.existing_guid,
                "new_tool_consumer_instance_guid": sentinel.new_guid,
            },
        )

    @pytest.fixture
    def assert_response(self, pyramid_request):
        def assert_response(template_data, status, message=None, error=None):
            assert pyramid_request.response.status_int == status

            if message:
                assert template_data == {"message": message}

            elif error:
                assert template_data == {"error": error}

            else:
                assert template_data == {}

        return assert_response
