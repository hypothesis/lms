from unittest import mock

import pytest
from h_matchers import Any

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.services import HAPIError
from lms.services.grading_info import GradingInfoService
from lms.services.h_api import HAPI
from lms.services.lti_h import LTIHService
from lms.validation.authentication._helpers._jwt import decode_jwt
from lms.values import HUser, LTIUser
from lms.views.basic_lti_launch import BasicLTILaunchViews


class TestBasicLTILaunch:
    """
    Test behavior common to all LTI launches.
    """

    def test_it_configures_frontend(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request)

    def test_it_does_not_configure_grading_if_request_unqualified(
        self, context, pyramid_request
    ):
        BasicLTILaunchViews(context, pyramid_request)
        assert "lmsGrader" not in context.js_config.config

    @pytest.fixture
    def h_api(self, pyramid_config):
        svc = mock.create_autospec(HAPI, instance=True, spec_set=True)
        pyramid_config.register_service(svc, name="h_api")
        return svc


class ConfiguredLaunch:
    def make_request(self, context, pyramid_request):  # pragma: no cover
        raise NotImplementedError("Child tests must implement this function")

    def test_it_reports_lti_launches(self, context, pyramid_request, LtiLaunches):
        pyramid_request.params.update(
            {
                "context_id": "TEST_CONTEXT_ID",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            }
        )

        self.make_request(context, pyramid_request)

        LtiLaunches.add.assert_called_once_with(
            pyramid_request.db,
            pyramid_request.params["context_id"],
            pyramid_request.params["oauth_consumer_key"],
        )

    def test_it_calls_grading_info_upsert(
        self, context, pyramid_request, grading_info_service
    ):
        self.make_request(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_called_once_with(
            pyramid_request, h_user=context.h_user, lti_user=pyramid_request.lti_user
        )

    def test_it_does_not_call_grading_info_upsert_if_instructor(
        self, context, pyramid_request, grading_info_service
    ):
        pyramid_request.lti_user = LTIUser("USER_ID", "OAUTH_STUFF", roles="instructor")

        self.make_request(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_not_called()

    def test_it_does_not_call_grading_info_upsert_if_canvas(
        self, context, pyramid_request, grading_info_service
    ):
        pyramid_request.params["tool_consumer_info_product_family_code"] = "canvas"

        self.make_request(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_not_called()

    @pytest.fixture(autouse=True)
    def grading_info_service(self, pyramid_config):
        grading_info_service = mock.create_autospec(
            GradingInfoService, instance=True, spec_set=True
        )
        pyramid_config.register_service(grading_info_service, name="grading_info")
        return grading_info_service

    @pytest.fixture(autouse=True)
    def lti_h_service(self, pyramid_config):
        lti_h_service = mock.create_autospec(LTIHService, instance=True, spec_set=True)
        pyramid_config.register_service(lti_h_service, name="lti_h")
        return lti_h_service

    @pytest.fixture
    def LtiLaunches(self, patch):
        return patch("lms.views.basic_lti_launch.LtiLaunches")

    @pytest.fixture(autouse=True)
    def ModuleItemConfiguration(self, patch):
        return patch("lms.views.basic_lti_launch.ModuleItemConfiguration")


class TestCanvasFileBasicLTILaunch(ConfiguredLaunch):
    def make_request(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request).canvas_file_basic_lti_launch()

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("canvas_api.authorize", "/TEST_AUTHORIZE_URL")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            # file_id is always required by canvas_file_basic_lti_launch.
            "file_id": "TEST_FILE_ID",
        }
        return pyramid_request


class TestDBConfiguredBasicLTILaunch(ConfiguredLaunch):
    def make_request(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request).db_configured_basic_lti_launch()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            # db_configured_basic_lti_launch() always needs resource_link_id
            # and tool_consumer_instance_guid.
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }
        return pyramid_request


class TestURLConfiguredBasicLTILaunch(ConfiguredLaunch):
    def make_request(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request).url_configured_basic_lti_launch()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # url_configured_basic_lti_launch() always needs url.
        pyramid_request.parsed_params = {"url": "TEST_URL"}
        return pyramid_request


class TestConfigureModuleItem(ConfiguredLaunch):
    def test_it_saves_the_assignments_document_url_to_the_db(
        self, context, pyramid_request, ModuleItemConfiguration
    ):
        self.make_request(context, pyramid_request)

        ModuleItemConfiguration.set_document_url.assert_called_once_with(
            pyramid_request.db,
            "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "TEST_RESOURCE_LINK_ID",
            "TEST_DOCUMENT_URL",
        )

    def make_request(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request).configure_module_item()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }

        return pyramid_request


class TestUnconfiguredBasicLTILaunch:
    def _assert_authorization_valid_jwt(self, authorization, expected_values):
        assert authorization.startswith("Bearer ")
        assert (
            decode_jwt(authorization[len("Bearer ") :], "test_secret")
            == expected_values
        )

    @pytest.fixture
    def pyramid_request(self, context, pyramid_request):
        pyramid_request.params = {
            "user_id": "TEST_USER_ID",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "context_id": "TEST_CONTEXT_ID",
        }
        return pyramid_request


class TestUnconfiguredBasicLTILaunchNotAuthorized:
    def test_it_returns_the_right_template_data(self, context, pyramid_request):
        data = BasicLTILaunchViews(
            context, pyramid_request
        ).unconfigured_basic_lti_launch_not_authorized()

        assert data == {}


@pytest.fixture
def context():
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
    context.js_config = mock.create_autospec(
        JSConfig, spec_set=True, instance=True, config={"urls": {}}
    )
    return context


@pytest.fixture
def lti_outcome_params():
    # Request params needed for calls to the LMS's Outcome Management service,
    # present when a student launches an assignment.
    #
    # These params are typically not present when a teacher launches an
    # assignment.
    return {
        "lis_result_sourcedid": "modelstudent-assignment1",
        "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
        "tool_consumer_info_product_family_code": "canvas",
    }
