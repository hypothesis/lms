from unittest.mock import sentinel

import pytest

from lms.product import Product
from lms.resources import LTILaunchResource
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "application_instance_service",
    "assignment_service",
    "course_service",
)


class TestLTILaunchResource:
    def test_application_instance(self, lti_launch, application_instance_service):
        assert (
            lti_launch.application_instance
            == application_instance_service.get_current.return_value
        )

    @pytest.mark.parametrize(
        "product,expected",
        [
            (Product.Family.CANVAS, True),
            (Product.Family.BLACKBOARD, False),
            (Product.Family.UNKNOWN, False),
        ],
    )
    def test_is_canvas(self, pyramid_request, product, expected):
        pyramid_request.product.family = product

        assert LTILaunchResource(pyramid_request).is_canvas == expected

    def test_js_config(self, pyramid_request, JSConfig):
        lti_launch = LTILaunchResource(pyramid_request)

        js_config = lti_launch.js_config

        JSConfig.assert_called_once_with(lti_launch, pyramid_request)
        assert js_config == JSConfig.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = pyramid_request.lti_params = {
            "tool_consumer_instance_guid": sentinel.tool_guid,
            "resource_link_id": sentinel.resource_link_id,
            "context_id": sentinel.context_id,
            "context_title": sentinel.context_title,
        }
        return pyramid_request

    @pytest.fixture
    def lti_launch(self, pyramid_request):
        return LTILaunchResource(pyramid_request)

    @pytest.fixture(autouse=True)
    def JSConfig(self, patch):
        return patch("lms.resources.lti_launch.JSConfig")
