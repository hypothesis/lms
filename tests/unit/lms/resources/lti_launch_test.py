from unittest import mock

import pytest
from pytest import param

from lms.models import ApplicationSettings, Grouping, Product
from lms.resources import LTILaunchResource
from lms.services import ApplicationInstanceNotFound

pytestmark = pytest.mark.usefixtures(
    "application_instance_service", "assignment_service"
)


class TestResourceLinkIdk:
    @pytest.mark.parametrize(
        "learner_id,get_id,lti_id,expected",
        [
            param(None, None, "LTI_ID", "LTI_ID", id="regular"),
            param("USER_ID", "GET_ID", "LTI_ID", "GET_ID", id="new_speedgrader"),
            param("USER_ID", None, "LTI_ID", "LTI_ID", id="old_speedgrader"),
        ],
    )
    def test_it(self, pyramid_request, learner_id, get_id, lti_id, expected):
        pyramid_request.GET = {
            "learner_canvas_user_id": learner_id,
            "resource_link_id": get_id,
        }
        with mock.patch.object(
            LTILaunchResource, "lti_params", {"resource_link_id": lti_id}
        ):
            assert LTILaunchResource(pyramid_request).resource_link_id == expected


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


class TestCustomCanvasAPIDomain:
    def test_it_returns_the_custom_canvas_api_domain(self, pyramid_request):
        lti_launch = LTILaunchResource(pyramid_request)

        assert lti_launch.custom_canvas_api_domain == "test_custom_canvas_api_domain"

    def test_it_returns_None_if_not_defined(self, pyramid_request):
        del pyramid_request.parsed_params["custom_canvas_api_domain"]

        lti_launch = LTILaunchResource(pyramid_request)

        custom_canvas_api_url = lti_launch.custom_canvas_api_domain
        assert custom_canvas_api_url is None

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "custom_canvas_api_domain": "test_custom_canvas_api_domain",
        }
        return pyramid_request


class TestJSConfig:
    def test_it_returns_the_js_config(self, pyramid_request, JSConfig):
        lti_launch = LTILaunchResource(pyramid_request)

        js_config = lti_launch.js_config

        JSConfig.assert_called_once_with(lti_launch, pyramid_request)
        assert js_config == JSConfig.return_value


@pytest.mark.usefixtures("has_course")
class TestSectionsEnabled:
    @pytest.mark.parametrize("is_canvas", [True, False])
    def test_support_for_canvas(self, lti_launch, is_canvas):
        with mock.patch.object(LTILaunchResource, "is_canvas", is_canvas):
            assert lti_launch.sections_enabled == is_canvas

    @pytest.mark.usefixtures("with_canvas")
    @pytest.mark.parametrize(
        "params,expected",
        (
            param(
                {
                    "focused_user": mock.sentinel.focused_user,
                    "learner_canvas_user_id": mock.sentinel.learner_canvas_user_id,
                },
                True,
                id="Speedgrader",
            ),
            param(
                {"focused_user": mock.sentinel.focused_user},
                False,
                id="Legacy Speedgrader",
            ),
        ),
    )
    def test_its_support_for_speedgrader(
        self, lti_launch, pyramid_request, params, expected
    ):
        pyramid_request.params.update(params)

        assert lti_launch.sections_enabled is expected

    @pytest.mark.usefixtures("with_canvas")
    def test_if_application_instance_service_raises(
        self, lti_launch, application_instance_service
    ):
        application_instance_service.get_current.side_effect = (
            ApplicationInstanceNotFound
        )
        assert not lti_launch.sections_enabled

    @pytest.mark.usefixtures("with_canvas")
    def test_it_depends_on_developer_key(
        self, lti_launch, application_instance_service
    ):
        application_instance_service.get_current.return_value.developer_key = None
        assert not lti_launch.sections_enabled

    @pytest.mark.usefixtures("with_canvas")
    @pytest.mark.parametrize("enabled", [True, False])
    def test_it_depends_on_course_setting(self, lti_launch, course_settings, enabled):
        course_settings.set("canvas", "sections_enabled", enabled)

        assert lti_launch.sections_enabled == enabled

    @pytest.fixture(autouse=True)
    def course_settings(self, course_service):
        settings = ApplicationSettings({"canvas": {"sections_enabled": True}})

        course_service.upsert_course.return_value.settings = settings

        return settings


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


class TestGroupSetId:
    @pytest.mark.usefixtures("with_blackboard")
    def test_blackboard_false_when_no_assignment(self, lti_launch, assignment_service):
        assignment_service.get_assignment.return_value = None

        assert not lti_launch.group_set_id

    @pytest.mark.usefixtures("with_blackboard")
    def test_blackboard_false_when_no_group_set(self, lti_launch, assignment_service):
        assignment_service.get_assignment.return_value.extra = {}

        assert not lti_launch.group_set_id

    @pytest.mark.usefixtures("with_blackboard")
    def test_blackboard(self, lti_launch, assignment_service):
        assignment_service.get_assignment.return_value.extra = {
            "group_set_id": mock.sentinel.id
        }

        assert lti_launch.group_set_id == mock.sentinel.id

    @pytest.mark.usefixtures("with_canvas")
    @pytest.mark.parametrize("group_set", ["", "not a number", None])
    def test_canvas_false_invalid_group_set_param(self, pyramid_request, group_set):
        pyramid_request.params.update({"group_set": group_set})

        assert not LTILaunchResource(pyramid_request).group_set_id

    @pytest.mark.usefixtures("with_canvas")
    def test_canvas(self, pyramid_request):
        pyramid_request.params.update({"group_set": 1})

        assert LTILaunchResource(pyramid_request).group_set_id == 1

    def test_other_lms(self, pyramid_request):
        pyramid_request.product.family = Product.Family.UNKNOWN

        assert not LTILaunchResource(pyramid_request).group_set_id

    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid"
        }
        return pyramid_request


class TestGroupingType:
    @pytest.mark.parametrize(
        "sections_enabled,group_set_id,expected",
        [
            (True, 1, Grouping.Type.GROUP),
            (True, None, Grouping.Type.SECTION),
            (False, 1, Grouping.Type.GROUP),
            (False, None, Grouping.Type.COURSE),
        ],
    )
    def test_it(self, sections_enabled, group_set_id, expected, lti_launch):

        with mock.patch.multiple(
            LTILaunchResource,
            sections_enabled=sections_enabled,
            group_set_id=group_set_id,
        ):
            assert lti_launch.grouping_type == expected


class TestLTIParams:
    def test_it_when_lti_jwt(self, lti_launch):
        assert lti_launch.lti_params == mock.sentinel.lti_params

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_params = mock.sentinel.lti_params
        return pyramid_request


@pytest.fixture
def lti_launch(pyramid_request):
    return LTILaunchResource(pyramid_request)


@pytest.fixture(autouse=True)
def JSConfig(patch):
    return patch("lms.resources.lti_launch.JSConfig")


@pytest.fixture
def has_course(pyramid_request):
    pyramid_request.parsed_params = {
        "context_id": "test_context_id",
        "context_title": "test_context_title",
        "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
    }


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.parsed_params = {}
    return pyramid_request


@pytest.fixture
def with_canvas(pyramid_request):
    pyramid_request.product.family = Product.Family.CANVAS


@pytest.fixture
def with_blackboard(pyramid_request):
    pyramid_request.product.family = Product.Family.BLACKBOARD
