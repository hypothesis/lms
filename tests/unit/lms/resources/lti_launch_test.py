from unittest import mock

import pytest
from pytest import param

from lms.models import ApplicationSettings
from lms.resources import LTILaunchResource
from lms.services import ApplicationInstanceNotFound

pytestmark = pytest.mark.usefixtures("application_instance_service", "course_service")


class TestHGroup:
    @pytest.mark.usefixtures("has_course")
    def test_it(self, lti_launch, course_service):
        course_service.upsert.return_value = mock.sentinel.course

        assert lti_launch.h_group == mock.sentinel.course


class TestResourceLinkIdk:
    @pytest.mark.parametrize(
        "learner_id,get_id,post_id,expected",
        [
            param(None, None, "POST_ID", "POST_ID", id="regular"),
            param("USER_ID", "GET_ID", "POST_ID", "GET_ID", id="new_speedgrader"),
            param("USER_ID", None, "POST_ID", "POST_ID", id="old_speedgrader"),
        ],
    )
    def test_it(self, pyramid_request, learner_id, get_id, post_id, expected):
        pyramid_request.POST = {
            "resource_link_id": post_id,
        }
        pyramid_request.GET = {
            "learner_canvas_user_id": learner_id,
            "resource_link_id": get_id,
        }
        assert LTILaunchResource(pyramid_request).resource_link_id == expected


class TestExtLTIAssignmentID:
    @pytest.mark.parametrize(
        "learner_id,get_id,post_id,expected",
        [
            param(None, None, "POST_ID", "POST_ID", id="regular"),
            param("USER_ID", "GET_ID", "POST_ID", "GET_ID", id="new_speedgrader"),
        ],
    )
    def test_it(self, pyramid_request, learner_id, get_id, post_id, expected):
        pyramid_request.POST = {
            "ext_lti_assignment_id": post_id,
        }
        pyramid_request.GET = {
            "learner_canvas_user_id": learner_id,
            "ext_lti_assignment_id": get_id,
        }
        assert LTILaunchResource(pyramid_request).ext_lti_assignment_id == expected


class TestIsLegacySpeedGrader:
    @pytest.mark.parametrize(
        "learner_id,get_resource_id,post_resource_id,context_id,expected",
        [
            param(
                None,
                "GET_ID",
                "POST_ID",
                "CONTEXT_ID",
                False,
                id="not speed grading",
            ),
            param(
                "USER_ID",
                "GET_ID",
                "WRONG_RESOURCE_LINK_ID",
                "WRONG_RESOURCE_LINK_ID",
                False,
                id="fixed speed grader",
            ),
            param(
                "USER_ID",
                None,
                "WRONG_RESOURCE_LINK_ID",
                "WRONG_RESOURCE_LINK_ID",
                True,
                id="legacy speed grader",
            ),
        ],
    )
    def test_it(
        self,
        pyramid_request,
        learner_id,
        get_resource_id,
        post_resource_id,
        context_id,
        expected,
    ):
        pyramid_request.POST = {
            "resource_link_id": post_resource_id,
            "context_id": context_id,
        }
        pyramid_request.GET = {
            "learner_canvas_user_id": learner_id,
            "resource_link_id": get_resource_id,
        }
        assert LTILaunchResource(pyramid_request).is_legacy_speedgrader == expected


class TestIsCanvas:
    @pytest.mark.parametrize(
        "parsed_params,is_canvas",
        [
            # For *some* launches Canvas includes a
            # `tool_consumer_info_product_family_code: canvas` and you can
            # detect Canvas that way.
            ({"tool_consumer_info_product_family_code": "canvas"}, True),
            # Some Canvas launches, e.g. content item selection launches, do
            # not have a tool_consumer_info_product_family_code param. In these
            # cases we can instead detect Canvas by the presence of its
            # custom_canvas_course_id param.
            ({"custom_canvas_course_id": mock.sentinel.whatever}, True),
            # Non-Canvas LMS's do also sometimes use
            # tool_consumer_info_product_family_code but they don't set it to
            # "canvas".
            ({"tool_consumer_info_product_family_code": "whiteboard"}, False),
            # If none of the recognized request params are present it should
            # fall back on "not Canvas".
            ({}, False),
        ],
    )
    def test_it(self, pyramid_request, parsed_params, is_canvas):
        pyramid_request.parsed_params = parsed_params

        assert LTILaunchResource(pyramid_request).is_canvas == is_canvas


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


class TestCanvasSectionsSupported:
    @pytest.mark.parametrize("is_canvas", [True, False])
    def test_support_for_canvas(self, lti_launch, is_canvas):
        with mock.patch.object(LTILaunchResource, "is_canvas", is_canvas):
            assert lti_launch.canvas_sections_supported() == is_canvas

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

        assert lti_launch.canvas_sections_supported() is expected

    def test_it_depends_on_application_instance_service(
        self, lti_launch, application_instance_service
    ):
        application_instance_service.get_current.return_value.developer_key = None
        assert not lti_launch.canvas_sections_supported()

    def test_if_application_instance_service_raises(
        self, lti_launch, application_instance_service
    ):
        application_instance_service.get_current.side_effect = (
            ApplicationInstanceNotFound
        )
        assert not lti_launch.canvas_sections_supported()

    @pytest.fixture(autouse=True)
    def sections_supported(self, pyramid_request):
        # We are in canvas
        pyramid_request.parsed_params[
            "tool_consumer_info_product_family_code"
        ] = "canvas"


@pytest.mark.usefixtures("has_course")
class TestCanvasSectionsEnabled:
    def test_its_enabled_when_everything_is_right(self, lti_launch, course_service):
        assert lti_launch.canvas_sections_enabled

        course_service.generate_authority_provided_id.assert_called_once()
        course_service.get_or_create.assert_called_with(
            course_service.generate_authority_provided_id.return_value
        )

    def test_its_disabled_if_sections_are_not_supported(
        self, lti_launch, canvas_sections_supported
    ):
        canvas_sections_supported.return_value = False
        assert not lti_launch.canvas_sections_enabled

    def test_its_disabled_if_the_course_settings_is_False(
        self, lti_launch, course_settings
    ):
        course_settings.set("canvas", "sections_enabled", False)
        assert not lti_launch.canvas_sections_enabled

    @pytest.fixture(autouse=True)
    def course_settings(self, course_service):
        settings = ApplicationSettings({"canvas": {"sections_enabled": True}})

        course_service.get_or_create.return_value.settings = settings

        return settings

    @pytest.fixture(autouse=True)
    def canvas_sections_supported(self):
        with mock.patch.object(
            LTILaunchResource, "canvas_sections_supported"
        ) as canvas_sections_supported:
            canvas_sections_supported.return_value = True
            yield canvas_sections_supported


class TestCourseExtra:
    # pylint: disable=protected-access
    def test_empty_in_non_canvas(self, pyramid_request):
        parsed_params = {}
        pyramid_request.parsed_params = parsed_params

        assert LTILaunchResource(pyramid_request)._course_extra() == {}

    def test_includes_course_id(self, pyramid_request):
        parsed_params = {
            "tool_consumer_info_product_family_code": "canvas",
            "custom_canvas_course_id": "ID",
        }
        pyramid_request.parsed_params = parsed_params

        assert LTILaunchResource(pyramid_request)._course_extra() == {
            "canvas": {"custom_canvas_course_id": "ID"}
        }


@pytest.mark.usefixtures("has_course")
class TestCanvasGroupsEnabled:
    def test_false_when_no_application_instance(
        self, application_instance_service, lti_launch
    ):
        application_instance_service.get_current.side_effect = (
            ApplicationInstanceNotFound
        )

        assert not lti_launch.canvas_groups_enabled

    @pytest.mark.parametrize("settings_value", [True, False])
    def test_returns_settings_value(
        self, settings_value, application_instance_service, lti_launch
    ):
        settings = ApplicationSettings({"canvas": {"groups_enabled": settings_value}})
        application_instance_service.get_current.return_value.settings = settings

        assert lti_launch.canvas_groups_enabled == settings_value


class TestCanvasIsGroupLaunch:
    def test_false_when_no_application_instance(self, lti_launch_groups_enabled):
        lti_launch_groups_enabled.canvas_groups_enabled = False

        assert not lti_launch_groups_enabled.canvas_is_group_launch

    @pytest.mark.parametrize("group_set", ["", "not a number", None])
    def test_false_invalid_group_set_param(
        self, pyramid_request, lti_launch_groups_enabled, group_set
    ):
        pyramid_request.params.update({"group_set": group_set})

        assert not lti_launch_groups_enabled.canvas_is_group_launch

    def test_it(self, pyramid_request, lti_launch_groups_enabled):
        pyramid_request.params.update({"group_set": 1})

        assert lti_launch_groups_enabled.canvas_is_group_launch

    @pytest.fixture
    def lti_launch_groups_enabled(self, pyramid_request):
        class TestableLTILaunchResource(LTILaunchResource):
            canvas_groups_enabled = True

        return TestableLTILaunchResource(pyramid_request)


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
