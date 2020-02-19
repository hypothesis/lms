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

    def test_it_adds_report_submission_config_if_required_params_present(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params.update(lti_outcome_params)

        BasicLTILaunchViews(context, pyramid_request)

        assert context.js_config.config["submissionParams"] == {
            "h_username": context.h_user.username,
            "lis_result_sourcedid": "modelstudent-assignment1",
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
        }

    @pytest.mark.parametrize(
        "key",
        [
            "lis_result_sourcedid",
            "lis_outcome_service_url",
            "tool_consumer_info_product_family_code",
        ],
    )
    def test_it_doesnt_add_report_submission_config_if_required_param_missing(
        self, context, pyramid_request, lti_outcome_params, key
    ):
        pyramid_request.params.update(lti_outcome_params)
        del pyramid_request.params[key]

        BasicLTILaunchViews(context, pyramid_request)

        assert "submissionParams" not in context.js_config.config

    def test_it_adds_report_submission_config_if_lms_not_canvas(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params.update(lti_outcome_params)
        pyramid_request.params.update(
            {"tool_consumer_info_product_family_code": "whiteboard"}
        )

        BasicLTILaunchViews(context, pyramid_request)

        assert "submissionParams" not in context.js_config.config

    def test_it_configures_client_to_focus_on_user_if_in_canvas_and_param_set(
        self, context, pyramid_request, h_api
    ):
        context.js_config.config["hypothesisClient"] = {}
        pyramid_request.params.update(
            {
                "tool_consumer_info_product_family_code": "canvas",
                "focused_user": "user123",
            }
        )
        h_api.get_user.return_value = HUser(
            authority="TEST_AUTHORITY", username="user123", display_name="Jim Smith"
        )

        BasicLTILaunchViews(context, pyramid_request)

        h_api.get_user.assert_called_once_with("user123")
        assert context.js_config.config["hypothesisClient"]["focus"] == {
            "user": {"username": "user123", "displayName": "Jim Smith"}
        }

    def test_it_uses_placeholder_display_name_for_focused_user_if_api_call_fails(
        self, context, pyramid_request, h_api
    ):
        context.js_config.config["hypothesisClient"] = {}
        pyramid_request.params.update(
            {
                "focused_user": "user123",
                "tool_consumer_info_product_family_code": "canvas",
            }
        )
        h_api.get_user.side_effect = HAPIError("User does not exist")

        BasicLTILaunchViews(context, pyramid_request)

        h_api.get_user.assert_called_once_with("user123")
        assert context.js_config.config["hypothesisClient"]["focus"] == {
            "user": {
                "username": "user123",
                "displayName": "(Couldn't fetch student name)",
            }
        }

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

    @pytest.fixture
    def frontend_app(self, patch):
        return patch("lms.views.basic_lti_launch.frontend_app")

    @pytest.fixture(autouse=True)
    def via_url(self, patch):
        return patch("lms.views.basic_lti_launch.via_url")

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
    def test_it_configures_via_callback_url(self, context, pyramid_request):
        self.make_request(context, pyramid_request)

        assert (
            context.js_config.config["urls"]["via_url_callback"]
            == "http://example.com/api/canvas/files/TEST_FILE_ID/via_url"
        )

    def test_it_configures_submission_params(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params.update(lti_outcome_params)

        self.make_request(context, pyramid_request)

        assert (
            context.js_config.config["submissionParams"]["canvas_file_id"]
            == "TEST_FILE_ID"
        )

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
    def test_it_configures_via_url(
        self,
        context,
        pyramid_request,
        lti_outcome_params,
        via_url,
        ModuleItemConfiguration,
    ):
        pyramid_request.params.update(lti_outcome_params)
        ModuleItemConfiguration.get_document_url.return_value = "TEST_DOCUMENT_URL"

        self.make_request(context, pyramid_request)

        ModuleItemConfiguration.get_document_url.assert_called_once_with(
            pyramid_request.db,
            "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "TEST_RESOURCE_LINK_ID",
        )
        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert context.js_config.config["urls"]["via_url"] == via_url.return_value
        assert (
            context.js_config.config["submissionParams"]["document_url"]
            == "TEST_DOCUMENT_URL"
        )

    def test_it_configures_frontend_grading(
        self, context, pyramid_request, frontend_app, via_url, ModuleItemConfiguration,
    ):
        self.make_request(context, pyramid_request)
        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config.config
        )

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
    def test_it_configures_via_url(
        self, context, pyramid_request, lti_outcome_params, via_url
    ):
        pyramid_request.params.update(lti_outcome_params)

        self.make_request(context, pyramid_request)

        via_url.assert_called_once_with(pyramid_request, "TEST_URL")
        assert context.js_config.config["urls"]["via_url"] == via_url.return_value
        assert (
            context.js_config.config["submissionParams"]["document_url"] == "TEST_URL"
        )

    def test_it_configures_frontend_grading(
        self,
        context,
        pyramid_request,
        frontend_app,
        lti_outcome_params,
        via_url,
        ModuleItemConfiguration,
    ):
        pyramid_request.params = {
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            **lti_outcome_params,
        }

        self.make_request(context, pyramid_request)

        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config.config
        )

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

    def test_it_configures_via_url(self, context, pyramid_request, via_url):
        self.make_request(context, pyramid_request)

        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert context.js_config.config["urls"]["via_url"] == via_url.return_value

    def test_it_configures_frontend_grading(
        self, context, pyramid_request, frontend_app, via_url, ModuleItemConfiguration,
    ):
        self.make_request(context, pyramid_request)

        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config.config
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
    def test_it_sets_the_right_javascript_config_settings(
        self, context, pyramid_request
    ):
        pyramid_request.params.update({"some_random_rubbish": "SOME_RANDOM_RUBBISH"})

        pyramid_request.registry.settings["google_client_id"] = "TEST_GOOGLE_CLIENT_ID"
        pyramid_request.registry.settings[
            "google_developer_key"
        ] = "TEST_GOOGLE_DEVELOPER_KEY"

        BasicLTILaunchViews(context, pyramid_request).unconfigured_basic_lti_launch()

        assert context.js_config.config == {
            "enableLmsFilePicker": False,
            "formAction": "http://example.com/module_item_configurations",
            "formFields": Any.dict(),
            "googleClientId": "TEST_GOOGLE_CLIENT_ID",
            "googleDeveloperKey": "TEST_GOOGLE_DEVELOPER_KEY",
            "customCanvasApiDomain": context.custom_canvas_api_domain,
            "lmsUrl": context.lms_url,
            "urls": {},
        }

        form_fields = context.js_config.config["formFields"]

        # Test that we pass through parameters from the request made to us
        # onto the configure module item call
        assert form_fields == Any.dict.containing(
            {
                "authorization": Any.string(),
                "resource_link_id": "TEST_RESOURCE_LINK_ID",
                "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
                "user_id": "TEST_USER_ID",
                "context_id": "TEST_CONTEXT_ID",
                "some_random_rubbish": "SOME_RANDOM_RUBBISH",
            }
        )

        self._assert_authorization_valid_jwt(
            form_fields["authorization"],
            {
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
                "roles": "TEST_ROLES",
                "user_id": "TEST_USER_ID",
            },
        )

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
