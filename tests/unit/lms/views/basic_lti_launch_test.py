from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.views.basic_lti_launch import BasicLTILaunchViews
from tests import factories


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
    # predicate and URLConfiguredBasicLTILaunchSchema ensure this.
    pyramid_request.parsed_params = {"url": "TEST_URL"}

    views = BasicLTILaunchViews(context, pyramid_request)

    return views.url_configured_basic_lti_launch()


def unconfigured_basic_lti_launch_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.unconfigured_basic_lti_launch().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.unconfigured_basic_lti_launch(), and return whatever
    BasicLTILaunchViews.unconfigured_basic_lti_launch() returns.
    """
    views = BasicLTILaunchViews(context, pyramid_request)
    return views.unconfigured_basic_lti_launch()


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

    def test_it_sets_frontend_app_mode(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request)

        context.js_config.enable_lti_launch_mode.assert_called_once_with()

    def test_it_sets_the_focused_user(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request)

        context.js_config.maybe_set_focused_user.assert_called_once_with()


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

    @pytest.mark.usefixtures("user_is_learner")
    def test_it_calls_grading_info_upsert(
        self, context, pyramid_request, grading_info_service, view_caller
    ):
        view_caller(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_called_once_with(
            pyramid_request,
            h_user=pyramid_request.lti_user.h_user,
            lti_user=pyramid_request.lti_user,
        )

    def test_it_does_not_call_grading_info_upsert_if_instructor(
        self, context, pyramid_request, grading_info_service, view_caller
    ):
        pyramid_request.lti_user = factories.LTIUser(roles="instructor")

        view_caller(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_not_called()

    @pytest.mark.usefixtures("is_canvas")
    def test_it_does_not_call_grading_info_upsert_if_canvas(
        self, context, pyramid_request, grading_info_service, view_caller
    ):
        view_caller(context, pyramid_request)

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


class TestCourseRecording:
    def test_it_records_the_course_in_the_DB(
        self, context, pyramid_request, view_caller, course_service
    ):
        view_caller(context, pyramid_request)

        course_service.get_or_create.assert_called_once_with(
            context.h_group.authority_provided_id
        )

    @pytest.fixture(
        params=[
            canvas_file_basic_lti_launch_caller,
            db_configured_basic_lti_launch_caller,
            url_configured_basic_lti_launch_caller,
            unconfigured_basic_lti_launch_caller,
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


@pytest.mark.usefixtures("is_canvas")
class TestCanvasFileBasicLTILaunch:
    @pytest.mark.usefixtures("is_canvas")
    def test_it_adds_the_canvas_file_id(self, context, pyramid_request):
        canvas_file_basic_lti_launch_caller(context, pyramid_request)

        context.js_config.add_canvas_file_id.assert_called_once_with(
            pyramid_request.params["file_id"]
        )


class TestDBConfiguredBasicLTILaunch:
    def test_it_enables_frontend_grading(self, context, pyramid_request):
        db_configured_basic_lti_launch_caller(context, pyramid_request)

        context.js_config.maybe_enable_grading.assert_called_once_with()

    def test_it_adds_the_document_url(
        self, context, pyramid_request, ModuleItemConfiguration
    ):
        db_configured_basic_lti_launch_caller(context, pyramid_request)

        ModuleItemConfiguration.get_document_url.assert_called_once_with(
            pyramid_request.db, "TEST_GUID", "TEST_RESOURCE_LINK_ID"
        )
        context.js_config.add_document_url.assert_called_once_with(
            ModuleItemConfiguration.get_document_url.return_value
        )


class TestURLConfiguredBasicLTILaunch:
    def test_it_enables_frontend_grading(self, context, pyramid_request):
        url_configured_basic_lti_launch_caller(context, pyramid_request)

        context.js_config.maybe_enable_grading.assert_called_once_with()

    def test_it_adds_the_document_url(self, context, pyramid_request):
        url_configured_basic_lti_launch_caller(context, pyramid_request)

        context.js_config.add_document_url.assert_called_once_with(
            pyramid_request.parsed_params["url"]
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

    def test_it_enables_frontend_grading(self, context, pyramid_request):
        configure_module_item_caller(context, pyramid_request)

        context.js_config.maybe_enable_grading.assert_called_once_with()

    def test_it_adds_the_document_url(self, context, pyramid_request):
        configure_module_item_caller(context, pyramid_request)

        context.js_config.add_document_url.assert_called_once_with(
            pyramid_request.parsed_params["document_url"]
        )


class TestUnconfiguredBasicLTILaunch:
    def test_it_enables_content_item_selection_mode(
        self, BearerTokenSchema, bearer_token_schema, context, pyramid_request
    ):
        unconfigured_basic_lti_launch_caller(context, pyramid_request)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        context.js_config.enable_content_item_selection_mode.assert_called_once_with(
            form_action="http://example.com/module_item_configurations",
            form_fields=dict(
                self.form_fields(),
                authorization=bearer_token_schema.authorization_param.return_value,
            ),
        )

    def form_fields(self):
        return {
            "user_id": "TEST_USER_ID",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "context_id": "TEST_CONTEXT_ID",
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = dict(
            self.form_fields(),
            oauth_nonce="TEST_OAUTH_NONCE",
            oauth_timestamp="TEST_OAUTH_TIMESTAMP",
            oauth_signature="TEST_OAUTH_SIGNATURE",
        )
        return pyramid_request


class TestUnconfiguredBasicLTILaunchNotAuthorized:
    def test_it_returns_the_right_template_data(self, context, pyramid_request):
        data = BasicLTILaunchViews(
            context, pyramid_request
        ).unconfigured_basic_lti_launch_not_authorized()

        assert data == {}


pytestmark = pytest.mark.usefixtures(
    "ai_getter", "course_service", "h_api", "grading_info_service", "lti_h_service"
)


@pytest.fixture
def context():
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
    context.js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)
    context.is_canvas = False
    return context


@pytest.fixture
def is_canvas(context):
    """Set the LMS that launched us to Canvas."""
    context.is_canvas = True


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.params.update(
        {
            "lis_result_sourcedid": "modelstudent-assignment1",
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
        }
    )
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
