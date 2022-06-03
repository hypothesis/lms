from unittest import mock
from unittest.mock import Mock, sentinel

import pytest

from lms.models import LTIParams
from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.views.lti.basic_launch import BasicLaunchViews


@pytest.mark.usefixtures(
    "application_instance_service",
    "assignment_service",
    "course_service",
    "h_api",
    "grading_info_service",
    "lti_h_service",
)
class TestBasicLaunchViews:
    def test___init___(self, context, pyramid_request, application_instance_service):
        application_instance_service.get_current.return_value = Mock()

        BasicLaunchViews(context, pyramid_request)

        context.js_config.enable_lti_launch_mode.assert_called_once_with()
        context.js_config.maybe_set_focused_user.assert_called_once_with()

        application_instance_service.get_current.assert_called_once_with()
        application_instance = application_instance_service.get_current.return_value
        application_instance.update_lms_data.assert_called_once_with(context.lti_params)

    @pytest.mark.parametrize(
        "parsed_params,expected_extras",
        [
            ({}, {}),
            ({"group_set": 42}, {"group_set_id": 42}),
        ],
    )
    def test_configure_assignment(
        self,
        svc,
        assignment_service,
        context,
        pyramid_request,
        parsed_params,
        expected_extras,
        JSConfig,
        _do_launch,
    ):
        # The document_url, resource_link_id and tool_consumer_instance_guid parsed
        # params are always present when configure_assignment() is called.
        # ConfigureAssignmentSchema ensures this.
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }
        pyramid_request.parsed_params.update(parsed_params)

        svc.configure_assignment()

        assignment_service.upsert_assignment.assert_called_once_with(
            pyramid_request.parsed_params["document_url"],
            pyramid_request.parsed_params["tool_consumer_instance_guid"],
            pyramid_request.parsed_params["resource_link_id"],
            extra=expected_extras,
        )

        JSConfig._hypothesis_client.fget.cache_clear.assert_called_once_with()  # pylint: disable=protected-access
        # One in __init__, one in `configure_assignment`
        context.js_config.enable_lti_launch_mode.assert_has_calls(
            [mock.call(), mock.call()]
        )

        _do_launch.assert_called_once_with(
            document_url=pyramid_request.parsed_params["document_url"],
            grading_supported=True,
        )

    def test_db_configured_launch(self, svc, assignment_service, context, _do_launch):
        svc.db_configured_launch()

        assignment_service.get_assignment.assert_called_once_with(
            context.lti_params["tool_consumer_instance_guid"], context.resource_link_id
        )

        _do_launch.assert_called_once_with(
            document_url=assignment_service.get_assignment.return_value.document_url
        )

    def test_url_configured_launch(self, svc, pyramid_request, _do_launch):
        # The `url` parsed param is always present when
        # url_configured_launch() is called. The url_configured=True view
        # predicate and URLConfiguredLaunchSchema ensure this.
        pyramid_request.parsed_params = {"url": "TEST_URL"}

        svc.url_configured_launch()

        _do_launch.assert_called_once_with(
            document_url=pyramid_request.parsed_params["url"]
        )

    def test_unconfigured_launch(
        self, svc, BearerTokenSchema, context, pyramid_request, _store_lti_data
    ):
        context.lti_params = {
            "oauth_nonce": "STRIPPED",
            "oauth_timestamp": "STRIPPED",
            "oauth_signature": "STRIPPED",
            "id_token": "STRIPPED",
            "other_values": "REMAIN",
        }

        svc.unconfigured_launch()

        _store_lti_data.assert_called_once_with()

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        BearerTokenSchema.return_value.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        authorization = BearerTokenSchema.return_value.authorization_param.return_value

        context.js_config.enable_file_picker_mode.assert_called_once_with(
            form_action="http://example.com/assignment",
            form_fields={"other_values": "REMAIN", "authorization": authorization},
        )

    def test_unconfigured_launch_not_authorized(self, context, pyramid_request):
        assert not BasicLaunchViews(
            context, pyramid_request
        ).unconfigured_launch_not_authorized()

    def test_blackboard_copied_launch(
        self, svc, pyramid_request, BlackboardCopied, _course_copied_launch
    ):
        result = svc.blackboard_copied_launch()

        BlackboardCopied.get_original_resource_link_id.assert_called_once_with(
            pyramid_request
        )

        _course_copied_launch.assert_called_once_with(
            BlackboardCopied.get_original_resource_link_id.return_value
        )
        assert result == _course_copied_launch.return_value

    def test_brightspace_copied_launch(
        self, svc, pyramid_request, BrightspaceCopied, _course_copied_launch
    ):
        result = svc.brightspace_copied_launch()

        BrightspaceCopied.get_original_resource_link_id.assert_called_once_with(
            pyramid_request
        )

        _course_copied_launch.assert_called_once_with(
            BrightspaceCopied.get_original_resource_link_id.return_value
        )
        assert result == _course_copied_launch.return_value

    @pytest.mark.usefixtures("is_canvas")
    def test_canvas_file_launch(
        self, svc, context, pyramid_request, assignment_service, _do_launch
    ):
        context.lti_params["custom_canvas_course_id"] = "TEST_COURSE_ID"
        pyramid_request.params["file_id"] = "TEST_FILE_ID"

        svc.canvas_file_launch()

        course_id = context.lti_params["custom_canvas_course_id"]
        file_id = pyramid_request.params["file_id"]
        document_url = f"canvas://file/course/{course_id}/file_id/{file_id}"

        assignment_service.upsert_assignment.assert_called_once_with(
            document_url=document_url,
            tool_consumer_instance_guid=pyramid_request.params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=pyramid_request.params["resource_link_id"],
        )

        _do_launch.assert_called_once_with(
            document_url=document_url, grading_supported=False
        )

    def test_legacy_vitalsource_launch(
        self, svc, pyramid_request, VitalSourceService, _do_launch
    ):
        pyramid_request.params["book_id"] = "BOOK_ID"
        pyramid_request.params["cfi"] = "/cfi"

        svc.legacy_vitalsource_launch()

        VitalSourceService.generate_document_url.assert_called_once_with(
            book_id=pyramid_request.params["book_id"],
            cfi=pyramid_request.params["cfi"],
        )

        _do_launch.assert_called_once_with(
            document_url=VitalSourceService.generate_document_url.return_value,
            grading_supported=True,
        )

    def test__course_copied_launch(
        self, svc, assignment_service, context, pyramid_request, _do_launch
    ):
        # pylint: disable=protected-access
        svc._course_copied_launch(sentinel.original_resource_link_id)

        assignment_service.get_assignment.assert_called_once_with(
            pyramid_request.params["tool_consumer_instance_guid"],
            sentinel.original_resource_link_id,
        )

        assignment_service.upsert_assignment.assert_called_once_with(
            assignment_service.get_assignment.return_value.document_url,
            context.lti_params["tool_consumer_instance_guid"],
            context.lti_params["resource_link_id"],
        )

        _do_launch.assert_called_once_with(
            document_url=assignment_service.get_assignment.return_value.document_url
        )

    @pytest.mark.parametrize("grading_supported", (True, False))
    def test__do_launch(self, svc, context, _store_lti_data, grading_supported):
        # pylint: disable=protected-access
        result = svc._do_launch(
            sentinel.document_url, grading_supported=grading_supported
        )

        _store_lti_data.assert_called_once_with()

        if grading_supported:
            context.js_config.maybe_enable_grading.assert_called_once_with()
        else:
            context.js_config.maybe_enable_grading.assert_not_called()

        context.js_config.add_document_url.assert_called_once_with(
            sentinel.document_url
        )
        assert result == {}

    @pytest.mark.usefixtures("user_is_learner")
    def test__store_lti_data(
        self,
        svc,
        context,
        pyramid_request,
        lti_h_service,
        LtiLaunches,
        grading_info_service,
    ):
        svc._store_lti_data()  # pylint: disable=protected-access

        lti_h_service.sync.assert_called_once_with([context.course], context.lti_params)

        LtiLaunches.add.assert_called_once_with(
            pyramid_request.db,
            context.lti_params["context_id"],
            context.lti_params["oauth_consumer_key"],
        )

        grading_info_service.upsert_from_request.assert_called_once_with(
            pyramid_request
        )

    @pytest.mark.usefixtures("user_is_instructor")
    def test__store_lti_data_doesnt_update_grading_info_for_instructors(
        self, svc, grading_info_service
    ):
        svc._store_lti_data()  # pylint: disable=protected-access

        grading_info_service.upsert_from_request.assert_not_called()

    @pytest.mark.usefixtures("user_is_learner", "is_canvas")
    def test__store_lti_data_doesnt_update_grading_info_for_canvas(
        self, svc, grading_info_service
    ):
        svc._store_lti_data()  # pylint: disable=protected-access

        grading_info_service.upsert_from_request.assert_not_called()

    @pytest.fixture
    def svc(self, context, pyramid_request):
        return BasicLaunchViews(context, pyramid_request)

    @pytest.fixture
    def _course_copied_launch(self, svc):
        with mock.patch.object(svc, "_course_copied_launch") as _course_copied_launch:
            yield _course_copied_launch

    @pytest.fixture
    def _do_launch(self, svc):
        with mock.patch.object(svc, "_do_launch") as _do_launch:
            yield _do_launch

    @pytest.fixture
    def _store_lti_data(self, svc):
        with mock.patch.object(svc, "_store_lti_data") as _store_lti_data:
            yield _store_lti_data

    @pytest.fixture
    def is_canvas(self, context):
        """Set the LMS that launched us to Canvas."""
        context.is_canvas = True

    @pytest.fixture
    def context(self, pyramid_request):
        context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)
        context.is_canvas = False
        context.resource_link_id = pyramid_request.params["resource_link_id"]
        context.lti_params = LTIParams(pyramid_request.params)
        return context

    @pytest.fixture
    def BlackboardCopied(self, patch):
        return patch("lms.views.lti.basic_launch.BlackboardCopied")

    @pytest.fixture
    def BrightspaceCopied(self, patch):
        return patch("lms.views.lti.basic_launch.BrightspaceCopied")

    @pytest.fixture
    def LtiLaunches(self, patch):
        return patch("lms.views.lti.basic_launch.LtiLaunches")

    @pytest.fixture
    def VitalSourceService(self, patch):
        return patch("lms.views.lti.basic_launch.VitalSourceService")

    @pytest.fixture
    def JSConfig(self, patch):
        return patch("lms.views.lti.basic_launch.JSConfig")

    @pytest.fixture(autouse=True)
    def BearerTokenSchema(self, patch):
        return patch("lms.views.lti.basic_launch.BearerTokenSchema")
