from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.views.content_item_selection import content_item_selection


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

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "content_item_return_url": "TEST_CONTENT_ITEM_RETURN_URL",
            "lti_version": "TEST_LTI_VERSION",
            "custom_canvas_api_domain": "TEST_CUSTOM_CANVAS_API_DOMAIN",
            "custom_canvas_course_id": "TEST_CUSTOM_CANVAS_COURSE_ID",
        }
        return pyramid_request

    @pytest.fixture
    def context(self):
        context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = mock.create_autospec(
            JSConfig, spec_set=True, instance=True, config={}
        )
        return context


pytestmark = pytest.mark.usefixtures("lti_h_service")
