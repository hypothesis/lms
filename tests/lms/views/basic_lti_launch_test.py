from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.services import CanvasAPIError
from lms.services.canvas_api import CanvasAPIClient
from lms.views.basic_lti_launch import BasicLTILaunchViews


class TestCanvasFileBasicLTILaunch:
    def test_it_configures_frontend(self, context, pyramid_request):
        pyramid_request.params = {"file_id": "TEST_FILE_ID"}

        BasicLTILaunchViews(context, pyramid_request).canvas_file_basic_lti_launch()

        assert context.js_config["mode"] == "basic-lti-launch"
        assert context.js_config["authUrl"] == "http://example.com/TEST_AUTHORIZE_URL"
        assert context.js_config["lmsName"] == "Canvas"

    def test_it_adds_the_via_url_to_the_javascript_config(
        self, context, pyramid_request
    ):
        pyramid_request.params = {"file_id": "TEST_FILE_ID"}

        BasicLTILaunchViews(context, pyramid_request).canvas_file_basic_lti_launch()

        assert (
            context.js_config["urls"]["via_url"]
            == "http://example.com/api/canvas/files/TEST_FILE_ID/via_url"
        )

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("canvas_api.authorize", "/TEST_AUTHORIZE_URL")


class TestDBConfiguredBasicLTILaunch:
    def test_it_passes_the_right_via_url_to_the_template(
        self, context, pyramid_request, via_url, ModuleItemConfiguration
    ):
        pyramid_request.params = {
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }
        ModuleItemConfiguration.get_document_url.return_value = "TEST_DOCUMENT_URL"

        data = BasicLTILaunchViews(
            context, pyramid_request
        ).db_configured_basic_lti_launch()

        ModuleItemConfiguration.get_document_url.assert_called_once_with(
            pyramid_request.db,
            "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "TEST_RESOURCE_LINK_ID",
        )
        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert data["via_url"] == via_url.return_value


class TestURLConfiguredBasicLTILaunch:
    def test_it_passes_the_right_via_url_to_the_template(
        self, context, pyramid_request, via_url
    ):
        pyramid_request.params = {"url": "TEST_URL"}

        data = BasicLTILaunchViews(
            context, pyramid_request
        ).url_configured_basic_lti_launch()

        via_url.assert_called_once_with(pyramid_request, "TEST_URL")
        assert data["via_url"] == via_url.return_value


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

    def test_it_passes_the_right_via_url_to_the_template(
        self, context, pyramid_request, via_url
    ):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }

        data = BasicLTILaunchViews(context, pyramid_request).configure_module_item()

        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert data["via_url"] == via_url.return_value


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.views.basic_lti_launch.BearerTokenSchema")


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
