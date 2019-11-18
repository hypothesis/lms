import pytest

from lms.views.basic_lti_launch import BasicLTILaunchViews


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
            "customCanvasApiDomain": context.custom_canvas_api_domain,
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

    @pytest.fixture(autouse=True)
    def BearerTokenSchema(self, patch):
        return patch("lms.views.basic_lti_launch.BearerTokenSchema")

    @pytest.fixture
    def bearer_token_schema(self, BearerTokenSchema):
        return BearerTokenSchema.return_value


class TestUnconfiguredBasicLTILaunchNotAuthorized:
    def test_it_returns_the_right_template_data(self, context, pyramid_request):
        data = BasicLTILaunchViews(
            context, pyramid_request
        ).unconfigured_basic_lti_launch_not_authorized()

        assert data == {}
