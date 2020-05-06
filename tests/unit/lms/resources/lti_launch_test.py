from unittest import mock

import pytest
from pyramid.authorization import ACLAuthorizationPolicy

from lms.resources import LTILaunchResource


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
    def test_it(self, lti_launch, pyramid_request, HGroup, h_group_name):
        pyramid_request.parsed_params = {
            "context_id": "test_context_id",
            "context_title": "test_context_title",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }

        assert lti_launch.h_group == HGroup.return_value
        h_group_name.assert_called_once_with("test_context_title")
        HGroup.assert_called_once_with(
            name=h_group_name.return_value,
            authority_provided_id="d55a3c86dd79d390ec8dc6a8096d0943044ea268",
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


class TestShouldUseSectionGroups:
    @pytest.mark.parametrize(
        "params",
        [
            # If we're in Canvas and the application instance has a developer
            # key with sections enabled then sections should be enabled.
            dict(
                is_canvas=True,
                is_feature_flag_enabled=True,
                developer_key=mock.sentinel.developer_key,
                is_canvas_sections_enabled=True,
                should_use_section_groups=True,
            ),
            # If the feature flag is disabled then sections should be disabled.
            dict(
                is_canvas=True,
                is_feature_flag_enabled=False,
                developer_key=mock.sentinel.developer_key,
                is_canvas_sections_enabled=True,
                should_use_section_groups=False,
            ),
            # If we're not in Canvas then sections should be disabled.
            dict(
                is_canvas=False,
                is_feature_flag_enabled=True,
                developer_key=mock.sentinel.developer_key,
                is_canvas_sections_enabled=True,
                should_use_section_groups=False,
            ),
            # If sections is disabled for the application instance then
            # sections should be disabled.
            dict(
                is_canvas=True,
                is_feature_flag_enabled=True,
                developer_key=mock.sentinel.developer_key,
                is_canvas_sections_enabled=False,
                should_use_section_groups=False,
            ),
            # If the application instance doesn't have a developer key then
            # sections should be disabled.
            dict(
                is_canvas=True,
                is_feature_flag_enabled=True,
                developer_key=None,
                is_canvas_sections_enabled=True,
                should_use_section_groups=False,
            ),
        ],
    )
    def test_it(
        self, lti_launch, pyramid_request, params, ai_getter,
    ):
        pyramid_request.feature.return_value = params["is_feature_flag_enabled"]
        ai_getter.developer_key.return_value = params["developer_key"]
        ai_getter.canvas_sections_enabled.return_value = params[
            "is_canvas_sections_enabled"
        ]

        with mock.patch.object(LTILaunchResource, "is_canvas", params["is_canvas"]):
            assert (
                lti_launch.should_use_section_groups
                == params["should_use_section_groups"]
            )


pytestmark = pytest.mark.usefixtures("ai_getter")


@pytest.fixture
def lti_launch(pyramid_request):
    return LTILaunchResource(pyramid_request)


@pytest.fixture(autouse=True)
def h_group_name(patch):
    return patch("lms.resources.lti_launch.h_group_name")


@pytest.fixture(autouse=True)
def HGroup(patch):
    return patch("lms.resources.lti_launch.HGroup")


@pytest.fixture(autouse=True)
def JSConfig(patch):
    return patch("lms.resources.lti_launch.JSConfig")


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.parsed_params = {}
    return pyramid_request
