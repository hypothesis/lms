from unittest import mock

import pytest

from lms.models import ModuleItemConfiguration
from lms.services import CanvasAPIError
from lms.services.canvas_api import CanvasAPIClient
from lms.views.basic_lti_launch import BasicLTILaunchViews


class TestCanvasFileBasicLTILaunch:
    def test_it_gets_a_public_url_from_the_canvas_api(
        self, canvas_api_client, pyramid_request
    ):
        pyramid_request.params = {"file_id": "TEST_FILE_ID"}

        BasicLTILaunchViews(pyramid_request).canvas_file_basic_lti_launch()

        canvas_api_client.public_url.assert_called_once_with("TEST_FILE_ID")

    def test_it_passes_the_right_via_url_to_the_template(
        self, canvas_api_client, pyramid_request, via_url
    ):
        pyramid_request.params = {"file_id": "TEST_FILE_ID"}

        data = BasicLTILaunchViews(pyramid_request).canvas_file_basic_lti_launch()

        via_url.assert_called_once_with(
            pyramid_request, canvas_api_client.public_url.return_value
        )
        assert data["via_url"] == via_url.return_value

    def test_if_getting_the_public_url_from_Canvas_fails_it_doesnt_return_a_via_url(
        self, canvas_api_client, pyramid_request
    ):
        # If no via_url is passed to the template then the template renders a
        # "Hypothesis needs your authorization" message instead of a Via
        # iframe.
        canvas_api_client.public_url.side_effect = CanvasAPIError("Failed")
        pyramid_request.params = {"file_id": "TEST_FILE_ID"}

        data = BasicLTILaunchViews(pyramid_request).canvas_file_basic_lti_launch()

        assert data == {}

    @pytest.fixture(autouse=True)
    def canvas_api_client(self, pyramid_config):
        canvas_api_client = mock.create_autospec(
            CanvasAPIClient, spec_set=True, instance=True
        )
        pyramid_config.register_service(canvas_api_client, name="canvas_api_client")
        return canvas_api_client


class TestDBConfiguredBasicLTILaunch:
    def test_it_passes_the_right_via_url_to_the_template(
        self, pyramid_request, via_url
    ):
        pyramid_request.params = {
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }
        pyramid_request.db.add(
            ModuleItemConfiguration(
                resource_link_id="TEST_RESOURCE_LINK_ID",
                tool_consumer_instance_guid="TEST_TOOL_CONSUMER_INSTANCE_GUID",
                document_url="TEST_DOCUMENT_URL",
            )
        )

        data = BasicLTILaunchViews(pyramid_request).db_configured_basic_lti_launch()

        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert data["via_url"] == via_url.return_value


class TestURLConfiguredBasicLTILaunch:
    def test_it_passes_the_right_via_url_to_the_template(
        self, pyramid_request, via_url
    ):
        pyramid_request.params = {"url": "TEST_URL"}

        data = BasicLTILaunchViews(pyramid_request).url_configured_basic_lti_launch()

        via_url.assert_called_once_with(pyramid_request, "TEST_URL")
        assert data["via_url"] == via_url.return_value


class TestUnconfiguredBasicLTILaunch:
    def test_it_returns_the_right_template_data(
        self, BearerTokenSchema, bearer_token_schema, pyramid_request
    ):
        pyramid_request.params = {
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "context_id": "TEST_CONTEXT_ID",
        }
        data = BasicLTILaunchViews(pyramid_request).unconfigured_basic_lti_launch()

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        assert data == {
            "content_item_return_url": "http://example.com/module_item_configurations",
            "form_fields": {
                "authorization": bearer_token_schema.authorization_param.return_value,
                "resource_link_id": "TEST_RESOURCE_LINK_ID",
                "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
                "user_id": "TEST_USER_ID",
                "context_id": "TEST_CONTEXT_ID",
            },
        }


class TestUnconfiguredBasicLTILaunchNotAuthorized:
    def test_it_returns_the_right_template_data(self, pyramid_request):
        data = BasicLTILaunchViews(
            pyramid_request
        ).unconfigured_basic_lti_launch_not_authorized()

        assert data == {}


class TestConfigureModuleItem:
    def test_it_saves_the_assignments_document_url_to_the_db(self, pyramid_request):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }

        BasicLTILaunchViews(pyramid_request).configure_module_item()

        mic = (
            pyramid_request.db.query(ModuleItemConfiguration).filter_by(
                resource_link_id="TEST_RESOURCE_LINK_ID",
                tool_consumer_instance_guid="TEST_TOOL_CONSUMER_INSTANCE_GUID",
            )
        ).one_or_none()
        assert mic and mic.document_url == "TEST_DOCUMENT_URL"

    def test_it_passes_the_right_via_url_to_the_template(
        self, pyramid_request, via_url
    ):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }

        data = BasicLTILaunchViews(pyramid_request).configure_module_item()

        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert data["via_url"] == via_url.return_value


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.views.basic_lti_launch.BearerTokenSchema")


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture(autouse=True)
def via_url(patch):
    return patch("lms.views.basic_lti_launch.via_url")
