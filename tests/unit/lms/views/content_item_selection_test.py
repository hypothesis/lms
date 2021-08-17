from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.views.content_item_selection import (
    application_instance_reused_guid,
    content_item_selection,
)

pytestmark = pytest.mark.usefixtures(
    "application_instance_service", "course_service", "lti_h_service"
)


class TestContentItemSelection:
    def test_it_enables_content_item_selection_mode(self, context, pyramid_request):
        content_item_selection(context, pyramid_request)

        context.js_config.enable_content_item_selection_mode.assert_called_once_with(
            form_action="TEST_CONTENT_ITEM_RETURN_URL",
            form_fields={
                "lti_message_type": "ContentItemSelection",
                "lti_version": "TEST_LTI_VERSION",
            },
        )

    def test_it_records_the_course_in_the_DB(self, context, pyramid_request):
        content_item_selection(context, pyramid_request)

        context.get_or_create_course.assert_called_once_with()

    def test_reused_application_instance_guid_error(self, context, pyramid_request):
        pyramid_request.context = context

        application_instance_reused_guid(pyramid_request)

        js_config = pyramid_request.context.js_config
        js_config.enable_error_dialog_mode.assert_called_with(
            error_code=JSConfig.ErrorCode.REUSED_TOOL_GUID,
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "content_item_return_url": "TEST_CONTENT_ITEM_RETURN_URL",
            "lti_version": "TEST_LTI_VERSION",
        }
        return pyramid_request

    @pytest.fixture
    def context(self):
        context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)
        context.js_config.ErrorCode = JSConfig.ErrorCode
        return context
