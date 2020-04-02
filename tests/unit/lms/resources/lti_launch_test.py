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


class TestHDisplayName:
    @pytest.mark.parametrize(
        "name_parts,expected",
        [
            # It returns the full name if there is one.
            (["full", "given", "family"], "full"),
            # If there's no full name it concatenates given and family names.
            ([None, "given", "family"], "given family"),
            (["", "given", "family"], "given family"),
            ([" ", "given", "family"], "given family"),
            # If there's no full name or given name it uses just the family name.
            ([None, None, "family"], "family"),
            ([" ", "", "family"], "family"),
            # If there's no full name or family name it uses just the given name.
            ([None, "given", None], "given"),
            ([" ", "given", ""], "given"),
            # If there's nothing else it just returns "Anonymous".
            ([None, None, None], "Anonymous"),
            ([" ", " ", ""], "Anonymous"),
            # Test white space stripping
            ([" full  ", None, None], "full"),
            ([None, "  given ", None], "given"),
            ([None, None, "  family "], "family"),
            ([None, "  given  ", "  family  "], "given family"),
            # Test truncation
            (["x" * 100, None, None], "x" * 29 + "…"),
            ([None, "x" * 100, None], "x" * 29 + "…"),
            ([None, None, "x" * 100], "x" * 29 + "…"),
            ([None, "given" * 3, "family" * 3], "givengivengiven familyfamilyf…"),
        ],
    )
    def test_it(self, name_parts, expected, pyramid_request):
        parsed_params = {
            f"lis_person_name_{field}": part
            for field, part in zip(["full", "given", "family"], name_parts)
            if part is not None
        }

        pyramid_request.parsed_params.update(parsed_params)

        assert LTILaunchResource(pyramid_request).h_user.display_name == expected

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
            "user_id": "test_user_id",
        }
        return pyramid_request


class TestHAuthorityProvidedID:
    def test_it(self, lti_launch):
        assert (
            lti_launch.h_authority_provided_id
            == "d55a3c86dd79d390ec8dc6a8096d0943044ea268"
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "context_id": "test_context_id",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        return pyramid_request


class TestHGroupID:
    def test_it(self, lti_launch):
        assert (
            lti_launch.h_groupid
            == "group:d55a3c86dd79d390ec8dc6a8096d0943044ea268@TEST_AUTHORITY"
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "context_id": "test_context_id",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        return pyramid_request


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


class TestHGroupName:
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
    def test_it_returns_group_names_based_on_context_titles(
        self, context_title, expected_group_name, pyramid_request
    ):
        pyramid_request.parsed_params["context_title"] = context_title

        assert LTILaunchResource(pyramid_request).h_group_name == expected_group_name


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


class TestHProvider:
    def test_it_just_returns_the_tool_consumer_instance_guid(self, pyramid_request):
        provider = LTILaunchResource(pyramid_request).h_provider

        assert provider == "test_tool_consumer_instance_guid"

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        return pyramid_request


class TestHProviderUniqueID:
    def test_it_just_returns_the_user_id(self, pyramid_request):
        provider_unique_id = LTILaunchResource(pyramid_request).h_provider_unique_id

        assert provider_unique_id == "test_user_id"

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "user_id": "test_user_id",
        }
        return pyramid_request


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


class TestHUser:
    def test_username_is_a_30_char_string(self, pyramid_request):
        username = LTILaunchResource(pyramid_request).h_user.username

        assert isinstance(username, str)
        assert len(username) == 30

    @pytest.mark.parametrize("parameter", ["tool_consumer_instance_guid", "user_id"])
    def test_it_raises_if_a_required_parameter_is_missing(
        self, pyramid_request, parameter
    ):
        pyramid_request.parsed_params.pop(parameter)

    def test_userid(self, pyramid_request):
        userid = LTILaunchResource(pyramid_request).h_user.userid

        assert userid == "acct:16aa3b3e92cdfa53e5996d138a7013@TEST_AUTHORITY"

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
            "user_id": "test_user_id",
        }
        return pyramid_request


class TestProvisioningEnabled:
    def test_it_checks_whether_provisioning_is_enabled_for_the_request(
        self, ai_getter, lti_launch
    ):
        lti_launch.provisioning_enabled  # pylint:disable=pointless-statement

        ai_getter.provisioning_enabled.assert_called_once_with(
            "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"
        )

    @pytest.mark.parametrize("expected", [True, False])
    def test_it_returns_based_on_ai_getter_provisiioning(
        self, expected, ai_getter, lti_launch
    ):
        ai_getter.provisioning_enabled.return_value = expected

        assert lti_launch.provisioning_enabled is expected

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
        }
        return pyramid_request


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


class TestLMSURL:
    def test_it_returns_the_ApplicationInstances_lms_url(
        self, ai_getter, pyramid_request
    ):
        lti_launch = LTILaunchResource(pyramid_request)

        lms_url = lti_launch.lms_url
        ai_getter.lms_url.assert_called_once_with(
            "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"
        )
        assert lms_url == ai_getter.lms_url.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
        }
        return pyramid_request


pytestmark = pytest.mark.usefixtures("ai_getter")


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
