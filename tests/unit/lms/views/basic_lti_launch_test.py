from unittest import mock

import pytest

from lms.models import LTIParams
from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.views.basic_lti_launch import BasicLTILaunchViews
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "application_instance_service",
    "assignment_service",
    "course_service",
    "h_api",
    "grading_info_service",
    "lti_h_service",
)


def canvas_file_basic_lti_launch_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.legacy_canvas_file_basic_lti_launch().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.legacy_canvas_file_basic_lti_launch(), and return whatever
    BasicLTILaunchViews.legacy_canvas_file_basic_lti_launch() returns.
    """
    # The custom_canvas_course_id param is always present when
    # legacy_canvas_file_basic_lti_launch() is called: Canvas always includes this
    # param because we request it in our config.xml.
    context.lti_params["custom_canvas_course_id"] = "TEST_COURSE_ID"
    # The file_id param is always present when legacy_canvas_file_basic_lti_launch()
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


def blackboard_copied_basic_lti_launch_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.blackboard_copied_basic_lti_launch().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.blackboard_copied_basic_lti_launch(), and return
    whatever BasicLTILaunchViews.blackboard_copied_basic_lti_launch() returns.
    """
    pyramid_request.params["resource_link_id_history"] = "test_resource_link_id_history"
    views = BasicLTILaunchViews(context, pyramid_request)
    return views.blackboard_copied_basic_lti_launch()


def brightspace_copied_basic_lti_launch_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.brightspace_copied_basic_lti_launch().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.brightspace_copied_basic_lti_launch(), and return
    whatever BasicLTILaunchViews.brightspace_copied_basic_lti_launch() returns.
    """
    pyramid_request.params[
        "ext_d2l_resource_link_id_history"
    ] = "test_ext_d2l_resource_link_id_history"
    views = BasicLTILaunchViews(context, pyramid_request)
    return views.brightspace_copied_basic_lti_launch()


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


def legacy_vitalsource_lti_launch_caller(context, pyramid_request):
    """Call BasicLTILaunchViews.legacy_vitalsource_lti_launch()."""
    pyramid_request.params["book_id"] = "BOOK_ID"
    pyramid_request.params["cfi"] = "/cfi"

    views = BasicLTILaunchViews(context, pyramid_request)

    return views.legacy_vitalsource_lti_launch()


def unconfigured_basic_lti_launch_caller(context, pyramid_request):
    """
    Call BasicLTILaunchViews.unconfigured_basic_lti_launch().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.unconfigured_basic_lti_launch(), and return whatever
    BasicLTILaunchViews.unconfigured_basic_lti_launch() returns.
    """
    views = BasicLTILaunchViews(context, pyramid_request)
    return views.unconfigured_basic_lti_launch()


def configure_assignment_caller(context, pyramid_request, parsed_params=None):
    """
    Call BasicLTILaunchViews.configure_assignment().

    Set up the appropriate conditions and then call
    BasicLTILaunchViews.configure_assignment(), and return whatever
    BasicLTILaunchViews.configure_assignment() returns.
    """
    # The document_url, resource_link_id and tool_consumer_instance_guid parsed
    # params are always present when configure_assignment() is called.
    # ConfigureAssignmentSchema ensures this.
    pyramid_request.parsed_params = {
        "document_url": "TEST_DOCUMENT_URL",
        "resource_link_id": "TEST_RESOURCE_LINK_ID",
        "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
    }
    if parsed_params:
        pyramid_request.parsed_params.update(parsed_params)

    views = BasicLTILaunchViews(context, pyramid_request)

    return views.configure_assignment()


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
        self,
        context,
        pyramid_request,
        grading_info_service,
        view_caller,
    ):
        view_caller(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_called_once_with(
            pyramid_request
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
            blackboard_copied_basic_lti_launch_caller,
            brightspace_copied_basic_lti_launch_caller,
            url_configured_basic_lti_launch_caller,
            configure_assignment_caller,
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
        self, context, pyramid_request, view_caller
    ):
        view_caller(context, pyramid_request)

        context.get_or_create_course.assert_called_once_with()

    @pytest.fixture(
        params=[
            canvas_file_basic_lti_launch_caller,
            db_configured_basic_lti_launch_caller,
            blackboard_copied_basic_lti_launch_caller,
            brightspace_copied_basic_lti_launch_caller,
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
    def test_it(self, context, pyramid_request, assignment_service):
        canvas_file_basic_lti_launch_caller(context, pyramid_request)

        course_id = context.lti_params["custom_canvas_course_id"]
        file_id = pyramid_request.params["file_id"]

        assignment_service.upsert.assert_called_once_with(
            document_url=f"canvas://file/course/{course_id}/file_id/{file_id}",
            tool_consumer_instance_guid=pyramid_request.params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=pyramid_request.params["resource_link_id"],
        )


class TestDBConfiguredBasicLTILaunch:
    def test_it_enables_frontend_grading(self, context, pyramid_request):
        db_configured_basic_lti_launch_caller(context, pyramid_request)

        context.js_config.maybe_enable_grading.assert_called_once_with()

    def test_it_adds_the_document_url(
        self, assignment_service, context, pyramid_request
    ):
        db_configured_basic_lti_launch_caller(context, pyramid_request)

        context.js_config.add_document_url.assert_called_once_with(
            assignment_service.get.return_value.document_url
        )


@pytest.mark.parametrize(
    "caller,param_name",
    [
        (
            blackboard_copied_basic_lti_launch_caller,
            "resource_link_id_history",
        ),
        (
            brightspace_copied_basic_lti_launch_caller,
            "ext_d2l_resource_link_id_history",
        ),
    ],
)
class TestFooCopiedBasicLTILaunch:
    """Common tests for the *_copied_basic_lti_launch() views."""

    def test_it_copies_the_assignment_settings_and_adds_the_document_url(
        self, assignment_service, caller, context, param_name, pyramid_request
    ):
        caller(context, pyramid_request)

        # It gets the original assignment settings
        # from the DB.
        assignment_service.get.assert_called_once_with(
            pyramid_request.params["tool_consumer_instance_guid"],
            pyramid_request.params[param_name],
        )

        # It copies the assignment settings to the new resource_link_id in the
        # DB.
        assignment_service.upsert.assert_called_once_with(
            assignment_service.get.return_value.document_url,
            context.lti_params["tool_consumer_instance_guid"],
            context.lti_params["resource_link_id"],
        )

        # It adds the document URL to the JavaScript config.
        context.js_config.add_document_url.assert_called_once_with(
            assignment_service.get.return_value.document_url
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


class TestLegacyVitalSourceLtiLaunch:
    def test_it(self, context, pyramid_request):
        legacy_vitalsource_lti_launch_caller(context, pyramid_request)

        context.js_config.add_document_url.assert_called_once_with(
            "vitalsource://book/bookID/BOOK_ID/cfi//cfi",
        )


class TestConfigureAssignment:
    @pytest.mark.parametrize(
        "parsed_params,expected_extras",
        [
            (None, {}),
            ({"group_set": 42}, {"group_set_id": 42}),
        ],
    )
    def test_it(
        self,
        assignment_service,
        context,
        pyramid_request,
        parsed_params,
        expected_extras,
        JSConfig,
    ):
        configure_assignment_caller(context, pyramid_request, parsed_params)

        assignment_service.upsert.assert_called_once_with(
            pyramid_request.parsed_params["document_url"],
            pyramid_request.parsed_params["tool_consumer_instance_guid"],
            pyramid_request.parsed_params["resource_link_id"],
            extra=expected_extras,
        )
        context.js_config.add_document_url.assert_called_once_with(
            pyramid_request.parsed_params["document_url"]
        )
        context.js_config.maybe_enable_grading.assert_called_once_with()

        JSConfig._hypothesis_client.fget.cache_clear.assert_called_once_with()  # pylint: disable=protected-access
        # One in __init__, one in `configure_assignment`
        context.js_config.enable_lti_launch_mode.assert_has_calls(
            [mock.call(), mock.call()]
        )

    @pytest.fixture
    def JSConfig(self, patch):
        return patch("lms.views.basic_lti_launch.JSConfig")


class TestUnconfiguredBasicLTILaunch:
    def test_it_enables_content_item_selection_mode(
        self, BearerTokenSchema, bearer_token_schema, context, pyramid_request
    ):
        unconfigured_basic_lti_launch_caller(context, pyramid_request)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        context.js_config.enable_file_picker_mode.assert_called_once_with(
            form_action="http://example.com/assignment",
            form_fields=dict(
                {
                    "user_id": "TEST_USER_ID",
                    "resource_link_id": "TEST_RESOURCE_LINK_ID",
                    "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
                    "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
                    "context_id": "TEST_CONTEXT_ID",
                },
                authorization=bearer_token_schema.authorization_param.return_value,
            ),
        )

    @property
    def form_fields(self):
        return {
            "oauth_nonce": "TEST_OAUTH_NOCE",
            "oauth_timestamp": "TEST_OAUTH_TIMESTAMP",
            "oauth_signature": "TEST_OAUTH_SIGNATURE",
            "id_token": "TEST_ID_TOKEN",
            "user_id": "TEST_USER_ID",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "context_id": "TEST_CONTEXT_ID",
        }

    @pytest.fixture
    def context(self, context):
        context.lti_params = self.form_fields
        return context


class TestUnconfiguredBasicLTILaunchNotAuthorized:
    def test_it_returns_the_right_template_data(self, context, pyramid_request):
        data = BasicLTILaunchViews(
            context, pyramid_request
        ).unconfigured_basic_lti_launch_not_authorized()

        assert not data


@pytest.fixture
def context(pyramid_request):
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
    context.js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)
    context.is_canvas = False
    context.resource_link_id = pyramid_request.params["resource_link_id"]
    context.lti_params = LTIParams(pyramid_request.params)
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


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value
