from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.views.content_item_selection import content_item_selection


class TestContentItemSelection:
    def test_it_sets_the_authUrl_javascript_config_setting(
        self, context, pyramid_request
    ):
        content_item_selection(context, pyramid_request)

        assert context.js_config["authUrl"] == "http://example.com/TEST_AUTHORIZE_URL"

    def test_it_sets_the_formAction_javascript_config_setting(
        self, context, pyramid_request
    ):
        content_item_selection(context, pyramid_request)

        assert context.js_config["formAction"] == "TEST_CONTENT_ITEM_RETURN_URL"

    def test_it_sets_the_formFields_javascript_config_setting(
        self, context, pyramid_request
    ):
        content_item_selection(context, pyramid_request)

        assert context.js_config["formFields"] == {
            "lti_message_type": "ContentItemSelection",
            "lti_version": "TEST_LTI_VERSION",
        }

    def test_it_sets_the_google_javascript_config_settings(
        self, context, pyramid_request
    ):
        content_item_selection(context, pyramid_request)

        assert context.js_config["googleClientId"] == "fake_client_id"
        assert context.js_config["googleDeveloperKey"] == "fake_developer_key"

    def test_it_sets_the_lmsName_javascript_config_setting(
        self, context, pyramid_request
    ):
        content_item_selection(context, pyramid_request)

        assert context.js_config["lmsName"] == "Canvas"

    def test_it_sets_the_ltiLaunchUrl_javascript_config_setting(
        self, context, pyramid_request
    ):
        content_item_selection(context, pyramid_request)

        assert (
            context.js_config["ltiLaunchUrl"]
            == "http://example.com/TEST_LTI_LAUNCH_URL"
        )

    def test_it_sets_the_courseId_javascript_config_setting(
        self, context, helpers, pyramid_request
    ):
        content_item_selection(context, pyramid_request)

        helpers.canvas_files_available.assert_called_once_with(pyramid_request)
        assert context.js_config["courseId"] == "TEST_CUSTOM_CANVAS_COURSE_ID"

    def test_if_canvas_files_arent_available_for_this_application_instance_then_it_omits_course_id(
        self, context, helpers, pyramid_request
    ):
        helpers.canvas_files_available.return_value = False

        content_item_selection(context, pyramid_request)

        helpers.canvas_files_available.assert_called_once_with(pyramid_request)
        assert "courseId" not in context.js_config

    def test_it_sets_the_lmsUrl_javascript_config_setting(
        self, context, pyramid_request
    ):
        content_item_selection(context, pyramid_request)

        assert context.js_config["lmsUrl"] == context.lms_url

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "content_item_return_url": "TEST_CONTENT_ITEM_RETURN_URL",
            "lti_version": "TEST_LTI_VERSION",
            "custom_canvas_api_domain": "TEST_CUSTOM_CANVAS_API_DOMAIN",
            "custom_canvas_course_id": "TEST_CUSTOM_CANVAS_COURSE_ID",
        }
        return pyramid_request

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("lti_launches", "/TEST_LTI_LAUNCH_URL")
        pyramid_config.add_route("canvas_api.authorize", "/TEST_AUTHORIZE_URL")

    @pytest.fixture
    def context(self):
        context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = {}
        return context


@pytest.fixture(autouse=True)
def helpers(patch):
    helpers = patch("lms.views.content_item_selection.helpers")
    helpers.canvas_files_available.return_value = True
    return helpers
