from unittest.mock import patch, sentinel

import pytest

from lms.product import Product
from lms.resources import LTILaunchResource
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "application_instance_service",
    "assignment_service",
    "course_service",
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


class TestNewCourseExtra:
    # pylint: disable=protected-access
    def test_empty_in_non_canvas(self, pyramid_request):
        parsed_params = {}
        pyramid_request.parsed_params = parsed_params

        assert not LTILaunchResource(pyramid_request)._new_course_extra()

    @pytest.mark.usefixtures("with_canvas")
    def test_includes_course_id(self, pyramid_request):
        parsed_params = {
            "custom_canvas_course_id": "ID",
        }
        pyramid_request.parsed_params = parsed_params

        assert LTILaunchResource(pyramid_request)._new_course_extra() == {
            "canvas": {"custom_canvas_course_id": "ID"}
        }

    @pytest.fixture
    def with_canvas(self, pyramid_request):
        pyramid_request.product.family = Product.Family.CANVAS


class TestCourse:
    def test_it_when_existing(self, course_service, lti_launch):
        course_service.get_by_context_id.return_value = factories.Course(
            extra={"existing": "extra"}
        )

        course = lti_launch.course

        course_service.get_by_context_id.assert_called_once_with(
            sentinel.context_id,
        )
        course_service.upsert_course.assert_called_once_with(
            context_id=sentinel.context_id,
            name=sentinel.context_title,
            extra={"existing": "extra"},
        )
        assert course == course_service.upsert_course.return_value

    def test_it_when_new(self, course_service, lti_launch, _new_course_extra):
        course_service.get_by_context_id.return_value = None

        course = lti_launch.course

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        course_service.upsert_course.assert_called_once_with(
            context_id=sentinel.context_id,
            name=sentinel.context_title,
            extra=_new_course_extra.return_value,
        )
        assert course == course_service.upsert_course.return_value

    @pytest.fixture
    def _new_course_extra(self, lti_launch):
        with patch.object(lti_launch, "_new_course_extra", autospec=True) as patched:
            yield patched


class TestGroupingType:
    def test_it(
        self,
        grouping_service,
        lti_launch,
        assignment_service,
        pyramid_request,
        course,
    ):
        assert (
            lti_launch.grouping_type
            == grouping_service.get_launch_grouping_type.return_value
        )
        assignment_service.get_assignment.assert_called_once_with(
            sentinel.tool_guid, sentinel.resource_link_id
        )
        grouping_service.get_launch_grouping_type.assert_called_once_with(
            pyramid_request,
            lti_launch.course,
            assignment_service.get_assignment.return_value,
        )

    @pytest.fixture
    def course(self, lti_launch):
        with patch.object(lti_launch, "course", autospec=True) as patched:
            yield patched


@pytest.fixture
def lti_launch(pyramid_request):
    return LTILaunchResource(pyramid_request)


@pytest.fixture(autouse=True)
def JSConfig(patch):
    return patch("lms.resources.lti_launch.JSConfig")


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.parsed_params = pyramid_request.lti_params = {
        "tool_consumer_instance_guid": sentinel.tool_guid,
        "resource_link_id": sentinel.resource_link_id,
        "context_id": sentinel.context_id,
        "context_title": sentinel.context_title,
    }
    return pyramid_request
