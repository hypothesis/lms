from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.services import HAPIError
from lms.services.h_api_client import HAPIClient
from lms.views.basic_lti_launch import BasicLTILaunchViews
from lms.values import HUser


class TestBasicLTILaunch:
    """
    Test behavior common to all LTI launches.
    """

    def test_it_configures_frontend(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request)
        assert context.js_config["mode"] == "basic-lti-launch"

    def test_it_does_not_configure_grading_if_request_unqualified(
        self, context, pyramid_request
    ):
        BasicLTILaunchViews(context, pyramid_request)
        assert "lmsGrader" not in context.js_config

    def test_it_adds_report_submission_config_if_required_params_present(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params.update(lti_outcome_params)

        BasicLTILaunchViews(context, pyramid_request)

        assert context.js_config["submissionParams"] == {
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

        assert "submissionParams" not in context.js_config

    def test_it_adds_report_submission_config_if_lms_not_canvas(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params.update(lti_outcome_params)
        pyramid_request.params.update(
            {"tool_consumer_info_product_family_code": "whiteboard"}
        )

        BasicLTILaunchViews(context, pyramid_request)

        assert "submissionParams" not in context.js_config

    def test_it_configures_client_to_focus_on_user_if_param_set(
        self, context, pyramid_request, h_api_client
    ):
        context.hypothesis_config = {}
        pyramid_request.params.update({"focused_user": "user123"})
        h_api_client.get_user.return_value = HUser(
            authority="TEST_AUTHORITY", username="user123", display_name="Jim Smith"
        )

        BasicLTILaunchViews(context, pyramid_request)

        h_api_client.get_user.assert_called_once_with("user123")
        assert context.hypothesis_config["focus"] == {
            "user": {"username": "user123", "displayName": "Jim Smith"}
        }

    def test_it_uses_placeholder_display_name_for_focused_user_if_api_call_fails(
        self, context, pyramid_request, h_api_client
    ):
        context.hypothesis_config = {}
        pyramid_request.params.update({"focused_user": "user123"})
        h_api_client.get_user.side_effect = HAPIError("User does not exist")

        BasicLTILaunchViews(context, pyramid_request)

        h_api_client.get_user.assert_called_once_with("user123")
        assert context.hypothesis_config["focus"] == {
            "user": {
                "username": "user123",
                "displayName": "(Couldn't fetch student name)",
            }
        }

    @pytest.fixture
    def h_api_client(self, pyramid_config):
        svc = mock.create_autospec(HAPIClient, instance=True)
        pyramid_config.register_service(svc, name="h_api_client")
        return svc


class TestCanvasFileBasicLTILaunch:
    def test_it_configures_frontend(self, context, pyramid_request):
        pyramid_request.params = {"file_id": "TEST_FILE_ID"}

        BasicLTILaunchViews(context, pyramid_request).canvas_file_basic_lti_launch()

        assert context.js_config["authUrl"] == "http://example.com/TEST_AUTHORIZE_URL"
        assert context.js_config["lmsName"] == "Canvas"

    def test_it_configures_via_callback_url(self, context, pyramid_request):
        pyramid_request.params = {"file_id": "TEST_FILE_ID"}

        BasicLTILaunchViews(context, pyramid_request).canvas_file_basic_lti_launch()

        assert (
            context.js_config["urls"]["via_url_callback"]
            == "http://example.com/api/canvas/files/TEST_FILE_ID/via_url"
        )

    def test_it_configures_submission_params(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params = {"file_id": "TEST_FILE_ID", **lti_outcome_params}

        BasicLTILaunchViews(context, pyramid_request).canvas_file_basic_lti_launch()

        assert context.js_config["submissionParams"]["canvas_file_id"] == "TEST_FILE_ID"

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("canvas_api.authorize", "/TEST_AUTHORIZE_URL")


class TestDBConfiguredBasicLTILaunch:
    def test_it_configures_via_url(
        self,
        context,
        pyramid_request,
        lti_outcome_params,
        via_url,
        ModuleItemConfiguration,
    ):
        pyramid_request.params = {
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            **lti_outcome_params,
        }
        ModuleItemConfiguration.get_document_url.return_value = "TEST_DOCUMENT_URL"

        BasicLTILaunchViews(context, pyramid_request).db_configured_basic_lti_launch()

        ModuleItemConfiguration.get_document_url.assert_called_once_with(
            pyramid_request.db,
            "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "TEST_RESOURCE_LINK_ID",
        )
        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert context.js_config["urls"]["via_url"] == via_url.return_value
        assert (
            context.js_config["submissionParams"]["document_url"] == "TEST_DOCUMENT_URL"
        )

    def test_it_configures_frontend_grading_if_feature_enabled(
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
        pyramid_request.feature = lambda feature: feature == "blackboard_grading"

        BasicLTILaunchViews(context, pyramid_request).db_configured_basic_lti_launch()
        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config
        )


class TestURLConfiguredBasicLTILaunch:
    def test_it_configures_via_url(
        self, context, pyramid_request, lti_outcome_params, via_url
    ):
        pyramid_request.params.update(**lti_outcome_params)
        pyramid_request.parsed_params = {"url": "TEST_URL"}

        BasicLTILaunchViews(context, pyramid_request).url_configured_basic_lti_launch()

        via_url.assert_called_once_with(pyramid_request, "TEST_URL")
        assert context.js_config["urls"]["via_url"] == via_url.return_value
        assert context.js_config["submissionParams"]["document_url"] == "TEST_URL"

    def test_it_configures_frontend_grading_if_feature_enabled(
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
        pyramid_request.parsed_params = {"url": "TEST_URL"}
        pyramid_request.feature = lambda feature: feature == "blackboard_grading"

        BasicLTILaunchViews(context, pyramid_request).url_configured_basic_lti_launch()
        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config
        )


class TestUnconfiguredBasicLTILaunch:
    def test_it_sets_the_right_javascript_config_settings(
        self, BearerTokenSchema, bearer_token_schema, context, pyramid_request
    ):
        pyramid_request.params[
            "custom_canvas_api_domain"
        ] = "TEST_CUSTOM_CANVAS_API_DOMAIN"
        pyramid_request.registry.settings["google_client_id"] = "TEST_GOOGLE_CLIENT_ID"
        pyramid_request.registry.settings[
            "google_developer_key"
        ] = "TEST_GOOGLE_DEVELOPER_KEY"

        BasicLTILaunchViews(context, pyramid_request).unconfigured_basic_lti_launch()

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        assert context.js_config == {
            "mode": "content-item-selection",
            "enableLmsFilePicker": False,
            "formAction": "http://example.com/module_item_configurations",
            "formFields": {
                "authorization": bearer_token_schema.authorization_param.return_value,
                "resource_link_id": "TEST_RESOURCE_LINK_ID",
                "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
                "user_id": "TEST_USER_ID",
                "context_id": "TEST_CONTEXT_ID",
            },
            "googleClientId": "TEST_GOOGLE_CLIENT_ID",
            "googleDeveloperKey": "TEST_GOOGLE_DEVELOPER_KEY",
            "lmsUrl": context.lms_url,
            "urls": {},
        }

    @pytest.fixture
    def pyramid_request(self, context, pyramid_request):
        pyramid_request.params = {
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
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


class TestConfigureModuleItem:
    def test_it_saves_the_assignments_document_url_to_the_db(
        self, context, pyramid_request, ModuleItemConfiguration
    ):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }

        BasicLTILaunchViews(context, pyramid_request).configure_module_item()

        ModuleItemConfiguration.set_document_url.assert_called_once_with(
            pyramid_request.db,
            "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "TEST_RESOURCE_LINK_ID",
            "TEST_DOCUMENT_URL",
        )

    def test_it_configures_via_url(self, context, pyramid_request, via_url):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }

        BasicLTILaunchViews(context, pyramid_request).configure_module_item()

        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert context.js_config["urls"]["via_url"] == via_url.return_value


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.views.basic_lti_launch.BearerTokenSchema")


@pytest.fixture
def frontend_app(patch):
    return patch("lms.views.basic_lti_launch.frontend_app")


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture
def context():
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
    context.js_config = {"urls": {}}
    return context


@pytest.fixture(autouse=True)
def ModuleItemConfiguration(patch):
    return patch("lms.views.basic_lti_launch.ModuleItemConfiguration")


@pytest.fixture(autouse=True)
def via_url(patch):
    return patch("lms.views.basic_lti_launch.via_url")


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
