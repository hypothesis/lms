from unittest import mock

import pytest
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.httpexceptions import HTTPBadRequest

from lms.resources import LTILaunchResource


class TestACL:
    def test_it_allows_LTI_users_to_launch_LTI_assignments(
        self, pyramid_config, pyramid_request
    ):
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy("TEST_USERNAME", groupids=["lti_user"])
        pyramid_config.set_authorization_policy(policy)

        context = LTILaunchResource(pyramid_request)

        assert pyramid_request.has_permission("launch_lti_assignment", context)

    def test_it_doesnt_allow_non_LTI_users_to_launch_LTI_assignments(
        self, pyramid_config, pyramid_request
    ):
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy("TEST_USERNAME", groupids=["foo", "bar"])
        pyramid_config.set_authorization_policy(policy)

        context = LTILaunchResource(pyramid_request)

        assert not pyramid_request.has_permission("launch_lti_assignment", context)


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
        params = {
            f"lis_person_name_{field}": part
            for field, part in zip(["full", "given", "family"], name_parts)
            if part is not None
        }

        pyramid_request.params.update(params)

        assert LTILaunchResource(pyramid_request).h_user.display_name == expected

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
            "user_id": "test_user_id",
        }
        return pyramid_request


class TestHAuthorityProvidedID:
    def test_it_raises_if_theres_no_tool_consumer_instance_guid(self, pyramid_request):
        pyramid_request.params.pop("tool_consumer_instance_guid")

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "tool_consumer_instance_guid" missing from LTI params',
        ):
            # pylint:disable=expression-not-assigned
            LTILaunchResource(pyramid_request).h_authority_provided_id

    def test_it_raises_if_theres_no_context_id(self, pyramid_request):
        pyramid_request.params.pop("context_id")

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "context_id" missing from LTI params',
        ):
            # pylint:disable=expression-not-assigned
            LTILaunchResource(pyramid_request).h_authority_provided_id

    def test_it(self, lti_launch):
        assert (
            lti_launch.h_authority_provided_id
            == "d55a3c86dd79d390ec8dc6a8096d0943044ea268"
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
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
        pyramid_request.params = {
            "context_id": "test_context_id",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        return pyramid_request


class TestHGroupName:
    def test_it_raises_if_theres_no_context_title(self, lti_launch):
        with pytest.raises(HTTPBadRequest):
            lti_launch.h_group_name  # pylint:disable=pointless-statement

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
        pyramid_request.params["context_title"] = context_title

        assert LTILaunchResource(pyramid_request).h_group_name == expected_group_name


class TestHProvider:
    def test_it_just_returns_the_tool_consumer_instance_guid(self, pyramid_request):
        provider = LTILaunchResource(pyramid_request).h_provider

        assert provider == "test_tool_consumer_instance_guid"

    @pytest.mark.parametrize(
        "request_params",
        [
            {},
            {"tool_consumer_instance_guid": ""},
            {"tool_consumer_instance_guid": None},
        ],
    )
    def test_it_raises_if_tool_consumer_instance_guid_is_missing(
        self, request_params, pyramid_request
    ):
        pyramid_request.params.pop("tool_consumer_instance_guid")
        pyramid_request.params.update(request_params)

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "tool_consumer_instance_guid" missing from LTI params',
        ):
            # pylint:disable=expression-not-assigned
            LTILaunchResource(pyramid_request).h_provider

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        return pyramid_request


class TestHProviderUniqueID:
    def test_it_just_returns_the_user_id(self, pyramid_request):
        provider_unique_id = LTILaunchResource(pyramid_request).h_provider_unique_id

        assert provider_unique_id == "test_user_id"

    @pytest.mark.parametrize("request_params", [{}, {"user_id": ""}, {"user_id": None}])
    def test_it_raises_if_user_id_is_missing(self, request_params, pyramid_request):
        pyramid_request.params.pop("user_id")
        pyramid_request.params.update(request_params)

        with pytest.raises(
            HTTPBadRequest, match='Required parameter "user_id" missing from LTI params'
        ):
            # pylint:disable=expression-not-assigned
            LTILaunchResource(pyramid_request).h_provider_unique_id

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "user_id": "test_user_id",
        }
        return pyramid_request


class TestIsCanvas:
    @pytest.mark.parametrize(
        "params,is_canvas",
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
    def test_it(self, pyramid_request, params, is_canvas):
        pyramid_request.params = params

        assert LTILaunchResource(pyramid_request).is_canvas == is_canvas


class TestHUser:
    def test_username_is_a_30_char_string(self, pyramid_request):
        username = LTILaunchResource(pyramid_request).h_user.username

        assert isinstance(username, str)
        assert len(username) == 30

    def test_it_raises_if_tool_consumer_instance_guid_is_missing(self, pyramid_request):
        pyramid_request.params.pop("tool_consumer_instance_guid")

        with pytest.raises(
            HTTPBadRequest,
            match='Required parameter "tool_consumer_instance_guid" missing from LTI params',
        ):
            # pylint:disable=expression-not-assigned
            LTILaunchResource(pyramid_request).h_user

    def test_it_raises_if_user_id_is_missing(self, pyramid_request):
        pyramid_request.params.pop("user_id")

        with pytest.raises(
            HTTPBadRequest, match='Required parameter "user_id" missing from LTI params'
        ):
            # pylint:disable=expression-not-assigned
            LTILaunchResource(pyramid_request).h_user

    def test_userid(self, pyramid_request):
        userid = LTILaunchResource(pyramid_request).h_user.userid

        assert userid == "acct:16aa3b3e92cdfa53e5996d138a7013@TEST_AUTHORITY"

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
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

    def test_it_returns_True_if_provisioning_enabled_for_application_instance(
        self, lti_launch
    ):
        assert lti_launch.provisioning_enabled is True

    def test_it_returns_False_if_provisioning_disabled_for_application_instance(
        self, ai_getter, lti_launch
    ):
        ai_getter.provisioning_enabled.return_value = False

        assert not lti_launch.provisioning_enabled

    def test_it_raises_if_no_oauth_consumer_key_in_params(self, pyramid_request):
        del pyramid_request.params["oauth_consumer_key"]
        lti_launch = LTILaunchResource(pyramid_request)

        with pytest.raises(HTTPBadRequest):
            lti_launch.provisioning_enabled  # pylint:disable=pointless-statement

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
        }
        return pyramid_request


class TestCustomCanvasAPIDomain:
    def test_it_returns_the_custom_canvas_api_domain(self, pyramid_request):
        lti_launch = LTILaunchResource(pyramid_request)

        assert lti_launch.custom_canvas_api_domain == "test_custom_canvas_api_domain"

    def test_it_returns_None_if_not_defined(self, pyramid_request):
        del pyramid_request.params["custom_canvas_api_domain"]

        lti_launch = LTILaunchResource(pyramid_request)

        custom_canvas_api_url = lti_launch.custom_canvas_api_domain
        assert custom_canvas_api_url is None

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
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
        pyramid_request.params = {
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
