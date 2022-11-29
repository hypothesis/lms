from unittest import mock

import pytest

from lms.product import Product
from lms.resources import LTILaunchResource

pytestmark = pytest.mark.usefixtures(
    "application_instance_service",
    "assignment_service",
)


class TestApplicationInstance:
    def test_it(self, lti_launch, application_instance_service):
        assert (
            lti_launch.application_instance
            == application_instance_service.get_current.return_value
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
    def test_it(self, pyramid_request, product, expected):
        pyramid_request.product.family = product

        assert LTILaunchResource(pyramid_request).is_canvas == expected


class TestJSConfig:
    def test_it_returns_the_js_config(self, pyramid_request, JSConfig):
        lti_launch = LTILaunchResource(pyramid_request)

        js_config = lti_launch.js_config

        JSConfig.assert_called_once_with(lti_launch, pyramid_request)
        assert js_config == JSConfig.return_value


class TestCourseExtra:
    # pylint: disable=protected-access
    def test_empty_in_non_canvas(self, pyramid_request):
        parsed_params = {}
        pyramid_request.parsed_params = parsed_params

        assert not LTILaunchResource(pyramid_request)._course_extra()

    @pytest.mark.usefixtures("with_canvas")
    def test_includes_course_id(self, pyramid_request):
        parsed_params = {
            "custom_canvas_course_id": "ID",
        }
        pyramid_request.parsed_params = parsed_params

        assert LTILaunchResource(pyramid_request)._course_extra() == {
            "canvas": {"custom_canvas_course_id": "ID"}
        }

    @pytest.fixture
    def with_canvas(self, pyramid_request):
        pyramid_request.product.family = Product.Family.CANVAS


class TestGroupingType:
    def test_it(
        self,
        grouping_service,
        lti_launch,
        course_service,
        assignment_service,
        pyramid_request,
    ):
        assert (
            lti_launch.grouping_type
            == grouping_service.get_launch_grouping_type.return_value
        )
        assignment_service.get_assignment.assert_called_once_with(
            mock.sentinel.tool_guid, mock.sentinel.resource_link_id
        )
        grouping_service.get_launch_grouping_type.assert_called_once_with(
            pyramid_request,
            course_service.upsert_course.return_value,
            assignment_service.get_assignment.return_value,
        )


@pytest.fixture
def lti_launch(pyramid_request):
    return LTILaunchResource(pyramid_request)


@pytest.fixture(autouse=True)
def JSConfig(patch):
    return patch("lms.resources.lti_launch.JSConfig")


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.parsed_params = pyramid_request.lti_params = {
        "tool_consumer_instance_guid": mock.sentinel.tool_guid,
        "resource_link_id": mock.sentinel.resource_link_id,
        "context_id": mock.sentinel.context_id,
        "context_title": mock.sentinel.context_title,
    }
    return pyramid_request
