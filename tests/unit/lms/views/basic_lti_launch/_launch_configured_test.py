import pytest

from lms.models import LtiLaunches
from lms.views.basic_lti_launch import BasicLTILaunchViews


class ConfiguredLaunchBaseClass:
    def assert_it_sends_lti_details_to_h(
        self, context, pyramid_request, LTIHypothesisBridge
    ):
        LTIHypothesisBridge.add_user_to_group.assert_called_once_with(
            context, pyramid_request
        )
        LTIHypothesisBridge.upsert_h_user.assert_called_once_with(
            context, pyramid_request
        )
        LTIHypothesisBridge.upsert_course_group.assert_called_once_with(
            context, pyramid_request
        )

    def assert_it_adds_an_lti_launch_record_to_the_db(self, pyramid_request):
        lti_launch = pyramid_request.db.query(LtiLaunches).one()

        assert lti_launch.context_id == "TEST_CONTEXT_ID"
        assert lti_launch.lti_key == "TEST_OAUTH_CONSUMER_KEY"

    @pytest.fixture(autouse=True)
    def LTIHypothesisBridge(self, patch):
        return patch("lms.views.basic_lti_launch.LTIHypothesisBridge")

    @pytest.fixture(autouse=True)
    def frontend_app(self, patch):
        return patch("lms.views.basic_lti_launch.frontend_app")


class TestCanvasFileBasicLTILaunch(ConfiguredLaunchBaseClass):
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

    def test_it_reports_values_to_h_api(
        self, context, pyramid_request, lti_outcome_params, LTIHypothesisBridge
    ):
        pyramid_request.params = {"file_id": "TEST_FILE_ID", **lti_outcome_params}

        BasicLTILaunchViews(context, pyramid_request).canvas_file_basic_lti_launch()

        self.assert_it_sends_lti_details_to_h(
            context, pyramid_request, LTIHypothesisBridge
        )
        self.assert_it_adds_an_lti_launch_record_to_the_db(pyramid_request)


class TestDBConfiguredBasicLTILaunch(ConfiguredLaunchBaseClass):
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

    def test_it_configures_frontend_grading(
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

        BasicLTILaunchViews(context, pyramid_request).db_configured_basic_lti_launch()
        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config
        )

    def test_it_reports_values_to_h_api(
        self, context, pyramid_request, lti_outcome_params, LTIHypothesisBridge
    ):
        pyramid_request.params = {
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            **lti_outcome_params,
        }

        BasicLTILaunchViews(context, pyramid_request).db_configured_basic_lti_launch()

        self.assert_it_sends_lti_details_to_h(
            context, pyramid_request, LTIHypothesisBridge
        )
        self.assert_it_adds_an_lti_launch_record_to_the_db(pyramid_request)


class TestURLConfiguredBasicLTILaunch(ConfiguredLaunchBaseClass):
    def test_it_configures_via_url(
        self, context, pyramid_request, lti_outcome_params, via_url,
    ):
        pyramid_request.params.update(**lti_outcome_params)
        pyramid_request.parsed_params = {"url": "TEST_URL"}

        BasicLTILaunchViews(context, pyramid_request).url_configured_basic_lti_launch()

        via_url.assert_called_once_with(pyramid_request, "TEST_URL")
        assert context.js_config["urls"]["via_url"] == via_url.return_value
        assert context.js_config["submissionParams"]["document_url"] == "TEST_URL"

    def test_it_configures_frontend_grading(
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

        BasicLTILaunchViews(context, pyramid_request).url_configured_basic_lti_launch()
        frontend_app.configure_grading.assert_called_once_with(
            pyramid_request, context.js_config
        )

    def test_it_reports_values_to_h_api(
        self, context, pyramid_request, lti_outcome_params, LTIHypothesisBridge
    ):
        pyramid_request.params = {
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            **lti_outcome_params,
        }
        pyramid_request.parsed_params = {"url": "TEST_URL"}

        BasicLTILaunchViews(context, pyramid_request).url_configured_basic_lti_launch()

        self.assert_it_sends_lti_details_to_h(
            context, pyramid_request, LTIHypothesisBridge
        )
        self.assert_it_adds_an_lti_launch_record_to_the_db(pyramid_request)
