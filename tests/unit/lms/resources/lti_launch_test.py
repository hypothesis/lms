from unittest import mock

import pytest
from pyramid.authorization import ACLAuthorizationPolicy

from lms.models import HGroup
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
    @pytest.mark.parametrize(
        "context_title,expected_group_name",
        (
            ("Test Course", "Test Course"),
            (" Test Course ", "Test Course"),
            ("Test   Course", "Test   Course"),
            ("Object Oriented Polymorphism 101", "Object Oriented Polymorp…"),
            ("  Object Oriented Polymorphism 101  ", "Object Oriented Polymorp…"),
        ),
    )
    def test_it(self, lti_launch, context_title, expected_group_name, pyramid_request):
        pyramid_request.parsed_params = {
            "context_id": "test_context_id",
            "context_title": context_title,
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }

        assert lti_launch.h_group == HGroup(
            expected_group_name, "d55a3c86dd79d390ec8dc6a8096d0943044ea268",
        )


class TestHSectionGroupID:
    @pytest.mark.parametrize(
        "settings,args,expected_groupid",
        (
            (
                {},
                {},
                "group:section-298e68dd4befff42f9a9ff7edffc542b2ba1f782@TEST_AUTHORITY",
            ),
            (
                {},
                {
                    "tool_consumer_instance_guid": "DIFFERENT_tool_consumer_instance_guid"
                },
                "group:section-e690bef466ef1d42587ae88b6b76f553d5e718e7@TEST_AUTHORITY",
            ),
            (
                {},
                {"context_id": "DIFFERENT_context_id"},
                "group:section-1ca5d17b0eab0e02784964c21aca33d99167402f@TEST_AUTHORITY",
            ),
            (
                {},
                {"section": {"id": "DIFFERENT_section_id"}},
                "group:section-15348ff2dbeb6e250d029c363007b8357bde7eea@TEST_AUTHORITY",
            ),
            (
                {"h_authority": "DIFFERENT_authority"},
                {},
                "group:section-298e68dd4befff42f9a9ff7edffc542b2ba1f782@DIFFERENT_authority",
            ),
        ),
    )
    def test_it(
        self, settings, args, expected_groupid, pyramid_request,
    ):
        pyramid_request.registry.settings.update(**settings)
        lti_launch_resource = LTILaunchResource(pyramid_request)
        args.setdefault("tool_consumer_instance_guid", "tool_consumer_instance_guid")
        args.setdefault("context_id", "context_id")
        args.setdefault("section", {"id": "section_id"})

        groupid = lti_launch_resource.h_section_groupid(**args)

        assert groupid == expected_groupid


class TestHSectionGroupName:
    @pytest.mark.parametrize(
        "section_name,group_name",
        [
            ("Test Section", "Test Section"),
            (" Test Section ", "Test Section"),
            ("Test   Section", "Test   Section"),
            ("Object Oriented Polymorphism 101", "Object Oriented Polymorp…"),
            ("  Object Oriented Polymorphism 101  ", "Object Oriented Polymorp…"),
        ],
    )
    def test_it(self, lti_launch, section_name, group_name):
        # A section dict as received from the Canvas API (except this one only
        # has the keys that we actually use).
        section = {"name": section_name}

        assert lti_launch.h_section_group_name(section) == group_name


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


@pytest.fixture
def lti_launch(pyramid_request):
    return LTILaunchResource(pyramid_request)


@pytest.fixture(autouse=True)
def JSConfig(patch):
    return patch("lms.resources.lti_launch.JSConfig")


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.parsed_params = {}
    return pyramid_request
