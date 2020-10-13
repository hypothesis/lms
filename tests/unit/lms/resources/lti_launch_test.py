from unittest import mock

import pytest
from pyramid.authorization import ACLAuthorizationPolicy
from pytest import param

from lms.models import ApplicationSettings
from lms.resources import LTILaunchResource

pytestmark = pytest.mark.usefixtures("ai_getter", "course_service")


class TestACL:
    @pytest.mark.parametrize(
        "principals,expected", ((["lti_user"], True), (["foo", "bar"], False))
    )
    def test_it_allows_the_correct_users_to_launch_LTI_assignments(
        self, pyramid_config, pyramid_request, principals, expected
    ):
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy("TEST_USERNAME", groupids=principals)
        pyramid_config.set_authorization_policy(policy)

        context = LTILaunchResource(pyramid_request)
        has_permission = pyramid_request.has_permission(
            "launch_lti_assignment", context
        )

        assert bool(has_permission) is expected


class TestHGroup:
    @pytest.mark.usefixtures("has_course")
    def test_it(self, lti_launch, HGroup, pyramid_request):
        assert lti_launch.h_group == HGroup.course_group.return_value

        HGroup.course_group.assert_called_once_with(
            course_name="test_context_title",
            tool_consumer_instance_guid=pyramid_request.parsed_params[
                "tool_consumer_instance_guid"
            ],
            context_id=pyramid_request.parsed_params["context_id"],
        )


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
    def test_its_supported_when_everything_is_right(self, lti_launch):
        assert lti_launch.canvas_sections_supported()

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

    def test_it_depends_on_ai_getter(self, lti_launch, ai_getter):
        ai_getter.canvas_sections_supported.return_value = False
        assert not lti_launch.canvas_sections_supported()

    @pytest.fixture(autouse=True)
    def sections_supported(self, ai_getter, pyramid_request):
        # We are in canvas
        pyramid_request.parsed_params[
            "tool_consumer_info_product_family_code"
        ] = "canvas"

        # The AI getter returns true
        ai_getter.canvas_sections_supported.return_value = True


@pytest.mark.usefixtures("has_course")
class TestCanvasSectionsEnabled:
    def test_its_enabled_when_everything_is_right(self, lti_launch, course_service):
        assert lti_launch.canvas_sections_enabled

        course_service.get_or_create.assert_called_once_with(
            lti_launch.h_group.authority_provided_id
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


@pytest.fixture
def lti_launch(pyramid_request):
    return LTILaunchResource(pyramid_request)


@pytest.fixture(autouse=True)
def HGroup(patch):
    return patch("lms.resources.lti_launch.HGroup")


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
