from unittest.mock import create_autospec, sentinel

import pytest
from pyramid import httpexceptions

from lms.models import ReusedConsumerKey
from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.services import HAPIError
from lms.validation import ValidationError
from lms.views.exceptions import ExceptionViews


class TestNotFound:
    def test_it(self, assert_response, exception_views):
        assert_response(exception_views.notfound(), 404, message="Page not found")

    @pytest.fixture
    def exception(self):
        return httpexceptions.HTTPNotFound()


class TestForbidden:
    def test_it(self, assert_response, exception_views):
        assert_response(
            exception_views.forbidden(),
            403,
            message="You're not authorized to view this page",
        )

    @pytest.fixture
    def exception(self):
        return httpexceptions.HTTPForbidden()


class TestHTTPClientError:
    def test_it(self, assert_response, exception, exception_views):
        assert_response(
            exception_views.http_client_error(),
            status=exception.status_int,
            message="http_client_error_test_explanation",
        )

    @pytest.fixture
    def exception(self):
        return httpexceptions.HTTPBadRequest("http_client_error_test_explanation")


class TestHAPIError:
    def test_it(self, assert_response, exception_views):
        assert_response(
            exception_views.hapi_error(), 500, message="hapi_error_test_explanation"
        )

    @pytest.fixture
    def exception(self):
        return HAPIError("hapi_error_test_explanation")


class TestValidationError:
    def test_it(self, assert_response, exception, exception_views):
        assert_response(
            exception_views.validation_error(),
            status=exception.status_int,
            error=exception,
        )

    @pytest.fixture
    def exception(self):
        return ValidationError(sentinel.messages)


class TestReusedToolGUIDError:
    def test_it(self, assert_response, exception_views, pyramid_request):
        assert_response(exception_views.reused_tool_guid_error(), 200)

        pyramid_request.context.js_config.enable_error_dialog_mode.assert_called_with(
            error_code=JSConfig.ErrorCode.REUSED_TOOL_GUID,
            error_details={
                "existing_tool_consumer_guid": sentinel.existing_guid,
                "new_tool_consumer_guid": sentinel.new_guid,
            },
        )

    @pytest.fixture
    def exception(self):
        return ReusedConsumerKey(sentinel.existing_guid, sentinel.new_guid)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
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
        return pyramid_request


class TestError:
    def test_it(self, assert_response, exception_views):
        assert_response(
            exception_views.error(),
            500,
            message="Sorry, but something went wrong. The issue has been "
            "reported and we'll try to fix it.",
        )

    @pytest.fixture
    def exception(self):
        return RuntimeError()


@pytest.fixture
def exception_views(exception, pyramid_request):
    return ExceptionViews(exception, pyramid_request)


@pytest.fixture
def assert_response(pyramid_request):
    def assert_response(template_data, status, message=None, error=None):
        assert pyramid_request.response.status_int == status

        if message:
            assert template_data == {"message": message}

        elif error:
            assert template_data == {"error": error}

        else:
            assert template_data == {}

    return assert_response
