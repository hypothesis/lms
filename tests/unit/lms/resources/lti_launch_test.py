from unittest import mock

import pytest

from lms.product import Product
from lms.resources import LTILaunchResource

pytestmark = pytest.mark.usefixtures(
    "application_instance_service", "assignment_service"
)


class TestIsCanvas:
    @pytest.mark.parametrize(
        "product,expected",
        [
            (Product.Family.CANVAS, True),
            (Product.Family.BLACKBOARD, False),
            (Product.Family.UNKNOWN, False),
        ],
    )
    def test_it(self, lti_launch, pyramid_request, product, expected):
        pyramid_request.product.family = product

        assert lti_launch.is_canvas == expected


class TestJSConfig:
    def test_it_returns_the_js_config(self, lti_launch, pyramid_request, JSConfig):
        js_config = lti_launch.js_config

        JSConfig.assert_called_once_with(lti_launch, pyramid_request)
        assert js_config == JSConfig.return_value


class TestCourseExtra:
    # pylint: disable=protected-access
    def test_empty_in_non_canvas(self, lti_launch, pyramid_request):
        pyramid_request.parsed_params = {}

        assert not lti_launch._course_extra()

    def test_includes_course_id(self, lti_launch, pyramid_request):
        pyramid_request.product.family = Product.Family.CANVAS
        pyramid_request.parsed_params = {"custom_canvas_course_id": "ID"}

        assert lti_launch._course_extra() == {
            "canvas": {"custom_canvas_course_id": "ID"}
        }


class TestGroupingType:
    def test_it(self, lti_launch, grouping_service):
        grouping_type = lti_launch.grouping_type

        grouping_service.get_grouping_type.assert_called_once_with()
        assert grouping_type == grouping_service.get_grouping_type.return_value


@pytest.fixture
def lti_launch(pyramid_request):
    return LTILaunchResource(pyramid_request)


@pytest.fixture(autouse=True)
def JSConfig(patch):
    return patch("lms.resources.lti_launch.JSConfig")
