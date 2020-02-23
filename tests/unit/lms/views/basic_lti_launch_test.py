from unittest import mock

import pytest
from h_matchers import Any

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.services import HAPIError
from lms.values import HUser, LTIUser
from lms.views.basic_lti_launch import BasicLTILaunchViews


def canvas_file_basic_lti_launch_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.canvas_file_basic_lti_launch().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.canvas_file_basic_lti_launch(), and return whatever
    BasicLTILaunchViews.canvas_file_basic_lti_launch() returns.
    """
    # The file_id param is always present when canvas_file_basic_lti_launch()
    # is called. The canvas_file=True view predicate ensures this.
    pyramid_request.params["file_id"] = "TEST_FILE_ID"

    views = BasicLTILaunchViews(context, pyramid_request)

    return views.canvas_file_basic_lti_launch()


def db_configured_basic_lti_launch_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.db_configured_basic_lti_launch().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.db_configured_basic_lti_launch(), and return whatever
    BasicLTILaunchViews.db_configured_basic_lti_launch() returns.
    """
    views = BasicLTILaunchViews(context, pyramid_request)
    return views.db_configured_basic_lti_launch()


def url_configured_basic_lti_launch_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.url_configured_basic_lti_launch().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.url_configured_basic_lti_launch(), and return whatever
    BasicLTILaunchViews.url_configured_basic_lti_launch() returns.
    """
    # The `url` parsed param is always present when
    # url_configured_basic_lti_launch() is called. The url_configured=True view
    # predicate and LaunchParamsURLConfiguredSchema ensure this.
    pyramid_request.parsed_params = {"url": "TEST_URL"}

    views = BasicLTILaunchViews(context, pyramid_request)

    return views.url_configured_basic_lti_launch()


def configure_module_item_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.configure_module_item().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.configure_module_item(), and return whatever
    BasicLTILaunchViews.configure_module_item() returns.
    """
    # The document_url, resource_link_id and tool_consumer_instance_guid parsed
    # params are always present when configure_module_item() is called.
    # ConfigureModuleItemSchema ensures this.
    pyramid_request.parsed_params = {
        "document_url": "TEST_DOCUMENT_URL",
        "resource_link_id": "TEST_RESOURCE_LINK_ID",
        "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
    }

    views = BasicLTILaunchViews(context, pyramid_request)

    return views.configure_module_item()


class TestBasicLTILaunchViewsInit:
    """Unit tests for BasicLTILaunchViews.__init__()."""

    def test_it_adds_report_submission_config_if_the_LMS_is_Canvas(
        self, context, canvas_request
    ):
        BasicLTILaunchViews(context, canvas_request)

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
        self, context, pyramid_request, key
    ):
        del pyramid_request.params[key]

        BasicLTILaunchViews(context, pyramid_request)

        assert "submissionParams" not in context.js_config.config

    def test_it_doesnt_add_report_submission_config_if_lms_not_canvas(
        self, context, pyramid_request
    ):
        BasicLTILaunchViews(context, pyramid_request)

        assert "submissionParams" not in context.js_config.config

    def test_it_configures_client_to_focus_on_user_if_in_canvas_and_param_set(
        self, context, canvas_request, h_api
    ):
        context.js_config.config["hypothesisClient"] = {}
        canvas_request.params["focused_user"] = "user123"
        h_api.get_user.return_value = HUser(
            authority="TEST_AUTHORITY", username="user123", display_name="Jim Smith"
        )

        BasicLTILaunchViews(context, canvas_request)

        h_api.get_user.assert_called_once_with("user123")
        assert context.js_config.config["hypothesisClient"]["focus"] == {
            "user": {"username": "user123", "displayName": "Jim Smith"}
        }

    def test_it_uses_placeholder_display_name_for_focused_user_if_api_call_fails(
        self, context, canvas_request, h_api
    ):
        context.js_config.config["hypothesisClient"] = {}
        canvas_request.params["focused_user"] = "user123"
        h_api.get_user.side_effect = HAPIError("User does not exist")

        BasicLTILaunchViews(context, canvas_request)

        h_api.get_user.assert_called_once_with("user123")
        assert context.js_config.config["hypothesisClient"]["focus"] == {
            "user": {
                "username": "user123",
                "displayName": "(Couldn't fetch student name)",
            }
        }


class TestCommon:
    """
    Tests common to multiple (but not all) BasicLTILaunchViews views.

    See the parametrized `view_caller` fixture below for the list of view
    methods that these tests apply to.
    """

    def test_it_reports_lti_launches(
        self, context, pyramid_request, LtiLaunches, view_caller
    ):
        pyramid_request.params.update(
            {
                "context_id": "TEST_CONTEXT_ID",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            }
        )

        view_caller(context, pyramid_request)

        LtiLaunches.add.assert_called_once_with(
            pyramid_request.db,
            pyramid_request.params["context_id"],
            pyramid_request.params["oauth_consumer_key"],
        )

    def test_it_calls_grading_info_upsert(
        self, context, pyramid_request, grading_info_service, view_caller
    ):
        view_caller(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_called_once_with(
            pyramid_request, h_user=context.h_user, lti_user=pyramid_request.lti_user
        )

    def test_it_does_not_call_grading_info_upsert_if_instructor(
        self, context, pyramid_request, grading_info_service, view_caller
    ):
        pyramid_request.lti_user = LTIUser("USER_ID", "OAUTH_STUFF", roles="instructor")

        view_caller(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_not_called()

    def test_it_does_not_call_grading_info_upsert_if_canvas(
        self, context, canvas_request, grading_info_service, view_caller
    ):
        view_caller(context, canvas_request)

        grading_info_service.upsert_from_request.assert_not_called()

    @pytest.fixture(
        params=[
            canvas_file_basic_lti_launch_caller,
            db_configured_basic_lti_launch_caller,
            url_configured_basic_lti_launch_caller,
            configure_module_item_caller,
        ]
    )
    def view_caller(self, request):
        """
        Return a function that calls the view method to be tested.

        This is a parametrized fixture. A test that uses this fixture will be
        run multiple times, once for each parametrized version of this fixture.

        See https://docs.pytest.org/en/latest/fixture.html#parametrizing-fixtures
        """
        return request.param


class TestCanvasFileBasicLTILaunch:
    def test_it_configures_frontend(self, context, canvas_request):
        canvas_file_basic_lti_launch_caller(context, canvas_request)

        assert context.js_config.config["lmsName"] == "Canvas"

    def test_it_configures_via_callback_url(self, context, canvas_request):
        canvas_file_basic_lti_launch_caller(context, canvas_request)

        assert (
            context.js_config.config["urls"]["via_url_callback"]
            == "http://example.com/api/canvas/files/TEST_FILE_ID/via_url"
        )

    def test_it_configures_submission_params(self, context, canvas_request):
        canvas_file_basic_lti_launch_caller(context, canvas_request)

        assert (
            context.js_config.config["submissionParams"]["canvas_file_id"]
            == "TEST_FILE_ID"
        )


class TestDBConfiguredBasicLTILaunch:
    def test_it_configures_via_url(
        self, context, canvas_request, via_url, ModuleItemConfiguration,
    ):
        ModuleItemConfiguration.get_document_url.return_value = "TEST_DOCUMENT_URL"

        db_configured_basic_lti_launch_caller(context, canvas_request)

        ModuleItemConfiguration.get_document_url.assert_called_once_with(
            canvas_request.db, "TEST_GUID", "TEST_RESOURCE_LINK_ID",
        )
        via_url.assert_called_once_with(canvas_request, "TEST_DOCUMENT_URL")
        assert context.js_config.config["urls"]["via_url"] == via_url.return_value
        assert (
            context.js_config.config["submissionParams"]["document_url"]
            == "TEST_DOCUMENT_URL"
        )

    def test_it_configures_frontend_grading(
        self, context, pyramid_request, frontend_app
    ):
        db_configured_basic_lti_launch_caller(context, pyramid_request)
        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config.config
        )


class TestURLConfiguredBasicLTILaunch:
    def test_it_configures_via_url(self, context, canvas_request, via_url):
        url_configured_basic_lti_launch_caller(context, canvas_request)

        via_url.assert_called_once_with(canvas_request, "TEST_URL")
        assert context.js_config.config["urls"]["via_url"] == via_url.return_value
        assert (
            context.js_config.config["submissionParams"]["document_url"] == "TEST_URL"
        )

    def test_it_configures_frontend_grading(
        self, context, pyramid_request, frontend_app
    ):
        url_configured_basic_lti_launch_caller(context, pyramid_request)

        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config.config
        )


class TestConfigureModuleItem:
    def test_it_saves_the_assignments_document_url_to_the_db(
        self, context, pyramid_request, ModuleItemConfiguration
    ):
        configure_module_item_caller(context, pyramid_request)

        ModuleItemConfiguration.set_document_url.assert_called_once_with(
            pyramid_request.db,
            "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "TEST_RESOURCE_LINK_ID",
            "TEST_DOCUMENT_URL",
        )

    def test_it_configures_via_url(self, context, pyramid_request, via_url):
        configure_module_item_caller(context, pyramid_request)

        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert context.js_config.config["urls"]["via_url"] == via_url.return_value

    def test_it_configures_frontend_grading(
        self, context, pyramid_request, frontend_app
    ):
        configure_module_item_caller(context, pyramid_request)

        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config.config
        )


class TestUnconfiguredBasicLTILaunch:
    def test_it_sets_the_right_javascript_config_settings(
        self, BearerTokenSchema, bearer_token_schema, context, pyramid_request
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
        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        assert form_fields == Any.dict.containing(
            {
                "authorization": bearer_token_schema.authorization_param.return_value,
                "resource_link_id": "TEST_RESOURCE_LINK_ID",
                "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
                "user_id": "TEST_USER_ID",
                "context_id": "TEST_CONTEXT_ID",
                "some_random_rubbish": "SOME_RANDOM_RUBBISH",
            }
        )

    def test_it_enables_content_item_selection_mode(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request).unconfigured_basic_lti_launch()

        context.js_config.enable_content_item_selection_mode.assert_called_once_with()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
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


pytestmark = pytest.mark.usefixtures("h_api", "grading_info_service", "lti_h_service")


@pytest.fixture
def context():
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
    context.js_config = mock.create_autospec(
        JSConfig, spec_set=True, instance=True, config={"urls": {}}
    )
    return context


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.params.update(
        {
            "lis_result_sourcedid": "modelstudent-assignment1",
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
        }
    )
    return pyramid_request


@pytest.fixture
def canvas_request(pyramid_request):
    pyramid_request.params["tool_consumer_info_product_family_code"] = "canvas"
    return pyramid_request


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.views.basic_lti_launch.BearerTokenSchema")


@pytest.fixture(autouse=True)
def LtiLaunches(patch):
    return patch("lms.views.basic_lti_launch.LtiLaunches")


@pytest.fixture(autouse=True)
def ModuleItemConfiguration(patch):
    return patch("lms.views.basic_lti_launch.ModuleItemConfiguration")


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture(autouse=True)
def frontend_app(patch):
    return patch("lms.views.basic_lti_launch.frontend_app")


@pytest.fixture(autouse=True)
def via_url(patch):
    return patch("lms.views.basic_lti_launch.via_url")
