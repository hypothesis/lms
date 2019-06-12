import pytest

from lms.views.content_item_selection import content_item_selection


class TestContentItemSelection:
    def test_it_passes_the_content_item_return_url_to_the_template(
        self, pyramid_request
    ):
        template_variables = content_item_selection(pyramid_request)

        assert (
            template_variables["content_item_return_url"]
            == "TEST_CONTENT_ITEM_RETURN_URL"
        )

    def test_it_passes_the_lti_launch_url_to_the_template(self, pyramid_request):
        template_variables = content_item_selection(pyramid_request)

        assert (
            template_variables["lti_launch_url"]
            == "http://example.com/TEST_LTI_LAUNCH_URL"
        )

    def test_it_passes_the_ContentItemSelection_form_fields_to_the_template(
        self, pyramid_request
    ):
        template_variables = content_item_selection(pyramid_request)

        assert template_variables["form_fields"] == {
            "lti_message_type": "ContentItemSelection",
            "lti_version": "TEST_LTI_VERSION",
        }

    def test_it_passes_the_Google_Picker_settings_to_the_template(
        self, pyramid_request
    ):
        template_variables = content_item_selection(pyramid_request)

        assert template_variables["google_client_id"] == "fake_client_id"
        assert template_variables["google_developer_key"] == "fake_developer_key"

    def test_it_passes_the_lms_url_to_the_template(self, pyramid_request):
        template_variables = content_item_selection(pyramid_request)

        assert template_variables["lms_url"] == "TEST_CUSTOM_CANVAS_API_DOMAIN"

    def test_if_theres_no_custom_canvas_api_domain_it_falls_back_on_the_application_instances_lms_url(
        self, ai_getter, pyramid_request
    ):
        del pyramid_request.params["custom_canvas_api_domain"]

        template_variables = content_item_selection(pyramid_request)

        ai_getter.lms_url.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key
        )
        assert template_variables["lms_url"] == ai_getter.lms_url.return_value

    def test_it_passes_the_course_id_to_the_template(self, helpers, pyramid_request):
        template_variables = content_item_selection(pyramid_request)

        helpers.canvas_files_available.assert_called_once_with(pyramid_request)
        assert template_variables["course_id"] == "TEST_CUSTOM_CANVAS_COURSE_ID"

    def test_if_canvas_files_arent_available_for_this_application_instance_then_it_omits_course_id(
        self, helpers, pyramid_request
    ):
        helpers.canvas_files_available.return_value = False

        template_variables = content_item_selection(pyramid_request)

        helpers.canvas_files_available.assert_called_once_with(pyramid_request)
        assert "course_id" not in template_variables

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


@pytest.fixture(autouse=True)
def helpers(patch):
    helpers = patch("lms.views.content_item_selection.helpers")
    helpers.canvas_files_available.return_value = True
    return helpers
