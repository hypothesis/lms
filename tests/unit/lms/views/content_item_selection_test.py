from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.services.lti_h import LTIHService
from lms.views.content_item_selection import content_item_selection


class TestContentItemSelection:
    def test_it_sets_the_authUrl_javascript_config_setting(
        self, context, pyramid_request, js_config
    ):
        content_item_selection(context, pyramid_request)

        assert js_config.config["authUrl"] == "http://example.com/TEST_AUTHORIZE_URL"

    def test_it_sets_the_formAction_javascript_config_setting(
        self, context, pyramid_request, js_config
    ):
        content_item_selection(context, pyramid_request)

        assert js_config.config["formAction"] == "TEST_CONTENT_ITEM_RETURN_URL"

    def test_it_sets_the_formFields_javascript_config_setting(
        self, context, pyramid_request, js_config
    ):
        content_item_selection(context, pyramid_request)

        assert js_config.config["formFields"] == {
            "lti_message_type": "ContentItemSelection",
            "lti_version": "TEST_LTI_VERSION",
        }

    def test_it_sets_the_google_javascript_config_settings(
        self, context, pyramid_request, js_config
    ):
        content_item_selection(context, pyramid_request)

        assert js_config.config["googleClientId"] == "fake_client_id"
        assert js_config.config["googleDeveloperKey"] == "fake_developer_key"

    def test_it_sets_the_lmsName_javascript_config_setting(
        self, context, pyramid_request, js_config
    ):
        content_item_selection(context, pyramid_request)

        assert js_config.config["lmsName"] == "Canvas"

    def test_it_sets_the_ltiLaunchUrl_javascript_config_setting(
        self, context, pyramid_request, js_config
    ):
        content_item_selection(context, pyramid_request)

        assert (
            js_config.config["ltiLaunchUrl"] == "http://example.com/TEST_LTI_LAUNCH_URL"
        )

    def test_it_sets_the_courseId_javascript_config_setting(
        self, context, helpers, pyramid_request, js_config
    ):
        content_item_selection(context, pyramid_request)

        helpers.canvas_files_available.assert_called_once_with(pyramid_request)
        assert js_config.config["courseId"] == "TEST_CUSTOM_CANVAS_COURSE_ID"

    @pytest.mark.parametrize("enable_picker", (True, False))
    def test_it_enables_lms_file_picker_if_canvas_files_available(
        self, context, helpers, pyramid_request, enable_picker, js_config
    ):
        helpers.canvas_files_available.return_value = enable_picker

        content_item_selection(context, pyramid_request)

        assert js_config.config["enableLmsFilePicker"] is enable_picker

    def test_if_canvas_files_arent_available_for_this_application_instance_then_it_omits_course_id(
        self, context, helpers, pyramid_request, js_config
    ):
        helpers.canvas_files_available.return_value = False

        content_item_selection(context, pyramid_request)

        helpers.canvas_files_available.assert_called_once_with(pyramid_request)
        assert "courseId" not in js_config.config

    def test_it_sets_the_lmsUrl_javascript_config_setting(
        self, context, pyramid_request, js_config
    ):
        content_item_selection(context, pyramid_request)

        assert js_config.config["lmsUrl"] == context.lms_url

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
        return mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)


@pytest.fixture(autouse=True)
def helpers(patch):
    helpers = patch("lms.views.content_item_selection.helpers")
    helpers.canvas_files_available.return_value = True
    return helpers


@pytest.fixture(autouse=True)
def lti_h_service(pyramid_config):
    lti_h_service = mock.create_autospec(LTIHService, instance=True, spec_set=True)
    pyramid_config.register_service(lti_h_service, name="lti_h")
    return lti_h_service
