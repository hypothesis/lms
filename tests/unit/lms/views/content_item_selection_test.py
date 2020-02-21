from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.services.lti_h import LTIHService
from lms.views.content_item_selection import content_item_selection


class TestContentItemSelection:
    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "content_item_return_url": "TEST_CONTENT_ITEM_RETURN_URL",
            "lti_version": "TEST_LTI_VERSION",
            "custom_canvas_api_domain": "TEST_CUSTOM_CANVAS_API_DOMAIN",
            "custom_canvas_course_id": "TEST_CUSTOM_CANVAS_COURSE_ID",
        }
        return pyramid_request

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("lti_launches", "/TEST_LTI_LAUNCH_URL")
        pyramid_config.add_route("canvas_api.authorize", "/TEST_AUTHORIZE_URL")

    @pytest.fixture
    def context(self):
        context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = mock.create_autospec(
            JSConfig, spec_set=True, instance=True, config={}
        )
        return context


@pytest.fixture(autouse=True)
def lti_h_service(pyramid_config):
    lti_h_service = mock.create_autospec(LTIHService, instance=True, spec_set=True)
    pyramid_config.register_service(lti_h_service, name="lti_h")
    return lti_h_service
