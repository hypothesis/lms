from unittest.mock import create_autospec, sentinel

import pytest
from pyramid import httpexceptions

from lms.models import ReusedConsumerKey
from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.security import DeniedWithException
from lms.services import HAPIError, SerializableError
from lms.validation import ValidationError
from lms.views.exceptions import ExceptionViews


class TestExceptionViews:
    def test_notfound(self, pyramid_request):
        exception = httpexceptions.HTTPNotFound()

        template_data = ExceptionViews(exception, pyramid_request).notfound()

        assert pyramid_request.response.status_int == 404
        assert template_data == {"message": "Page not found"}

    def test_forbidden(self, pyramid_request):
        exception = httpexceptions.HTTPForbidden()

        template_data = ExceptionViews(exception, pyramid_request).forbidden()

        assert pyramid_request.response.status_int == 403
        assert template_data == {"message": "You're not authorized to view this page"}

    def test_forbidden_with_validation_error(self, pyramid_request):
        exception = ValidationError(sentinel.messages)
        forbidden = httpexceptions.HTTPForbidden(result=DeniedWithException(exception))

        template_data = ExceptionViews(forbidden, pyramid_request).forbidden()

        assert (
            pyramid_request.override_renderer
            == "lms:templates/validation_error.html.jinja2"
        )
        assert pyramid_request.response.status_int == 403
        assert template_data == {"error": exception}

    @pytest.mark.usefixtures("js_config")
    def test_forbidden_with_serializable_error(self, pyramid_request):
        exception = SerializableError(
            error_code=sentinel.error_code,
            message=sentinel.message,
            details=sentinel.details,
        )
        forbidden = httpexceptions.HTTPForbidden(result=DeniedWithException(exception))

        template_data = ExceptionViews(forbidden, pyramid_request).forbidden()

        assert (
            pyramid_request.override_renderer
            == "lms:templates/error_dialog.html.jinja2"
        )
        assert pyramid_request.response.status_int == 400
        pyramid_request.context.js_config.enable_error_dialog_mode.assert_called_with(
            error_code=exception.error_code,
            error_details=exception.details,
            message=exception.message,
        )
        assert not template_data

    def test_http_client_error(self, pyramid_request):
        exception = httpexceptions.HTTPBadRequest(sentinel.message)

        template_data = ExceptionViews(exception, pyramid_request).http_client_error()

        assert pyramid_request.response.status_int == exception.status_int
        assert template_data == {"message": "sentinel.message"}

    def test_hapi_error(self, pyramid_request):
        exception = HAPIError(sentinel.message)

        template_data = ExceptionViews(exception, pyramid_request).hapi_error()

        assert pyramid_request.response.status_int == 500
        assert template_data == {"message": sentinel.message}

    def test_validation_error(self, pyramid_request):
        exception = ValidationError(sentinel.messages)

        template_data = ExceptionViews(exception, pyramid_request).validation_error()

        assert pyramid_request.response.status_int == exception.status_int
        assert template_data == {"error": exception}

    @pytest.mark.usefixtures("js_config")
    def test_serializable_error(self, pyramid_request):
        exception = SerializableError(
            error_code=sentinel.error_code,
            message=sentinel.message,
            details=sentinel.details,
        )

        template_data = ExceptionViews(exception, pyramid_request).serializable_error()

        pyramid_request.context.js_config.enable_error_dialog_mode.assert_called_with(
            error_code=exception.error_code,
            error_details=exception.details,
            message=exception.message,
        )
        assert not template_data
        assert pyramid_request.response.status_int == 400

    def test_error(self, pyramid_request):
        exception = RuntimeError()

        template_data = ExceptionViews(exception, pyramid_request).error()

        assert pyramid_request.response.status_int == 500
        assert template_data == {
            "message": "Sorry, but something went wrong. The issue has been reported and we'll try to fix it."
        }

    @pytest.mark.usefixtures("js_config")
    def test_reused_consumer_key(self, pyramid_request):
        exception = ReusedConsumerKey(sentinel.existing_guid, sentinel.new_guid)

        template_data = ExceptionViews(exception, pyramid_request).reused_consumer_key()

        pyramid_request.context.js_config.enable_error_dialog_mode.assert_called_with(
            error_code=JSConfig.ErrorCode.REUSED_CONSUMER_KEY,
            error_details={
                "existing_tool_consumer_instance_guid": sentinel.existing_guid,
                "new_tool_consumer_instance_guid": sentinel.new_guid,
            },
        )
        assert not template_data
        assert pyramid_request.response.status_int == 400

    @pytest.fixture
    def js_config(self, pyramid_request):
        js_config = create_autospec(
            JSConfig,
            instance=True,
            spec_set=True,
            ErrorCode=JSConfig.ErrorCode,
        )

        context = create_autospec(
            LTILaunchResource, instance=True, spec_set=True, js_config=js_config
        )
        pyramid_request.context = context

        return js_config
