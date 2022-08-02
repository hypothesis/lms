from unittest import mock
from unittest.mock import patch, sentinel

import pytest

from lms.models import LTIParams
from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.security import Permissions
from lms.views.lti.basic_launch import BasicLaunchViews, has_document_url
from tests import factories


class TestHasDocumentURL:
    @pytest.mark.parametrize("document_url", (None, "a_url"))
    def test_it(self, document_url_service, pyramid_request, document_url):
        document_url_service.get_document_url.return_value = document_url

        result = has_document_url(sentinel.context, pyramid_request)

        document_url_service.get_document_url.assert_called_once_with(pyramid_request)
        assert result == bool(document_url)


@pytest.mark.usefixtures(
    "assignment_service",
    "grading_info_service",
    "lti_h_service",
    "lti_role_service",
    "grouping_service",
)
class TestBasicLaunchViews:
    def test___init___(self, context, pyramid_request):
        BasicLaunchViews(context, pyramid_request)

        context.application_instance.check_guid_aligns.assert_called_once_with(
            pyramid_request.lti_params["tool_consumer_instance_guid"]
        )

    @pytest.mark.usefixtures("user_is_learner")
    def test__init__stores_data(
        self,
        context,
        pyramid_request,
        LtiLaunches,
        grading_info_service,
    ):
        BasicLaunchViews(context, pyramid_request)

        context.application_instance.update_lms_data.assert_called_once_with(
            pyramid_request.lti_params
        )

        LtiLaunches.add.assert_called_once_with(
            pyramid_request.db,
            pyramid_request.lti_params["context_id"],
            pyramid_request.lti_params["oauth_consumer_key"],
        )

        grading_info_service.upsert_from_request.assert_called_once_with(
            pyramid_request
        )

    @pytest.mark.usefixtures("user_is_instructor")
    def test__init___doesnt_update_grading_info_for_instructors(
        self, context, pyramid_request, grading_info_service
    ):
        BasicLaunchViews(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_not_called()

    @pytest.mark.usefixtures("user_is_learner", "is_canvas")
    def test__init___doesnt_update_grading_info_for_canvas(
        self, context, pyramid_request, grading_info_service
    ):
        BasicLaunchViews(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_not_called()

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
        pyramid_request,
        parsed_params,
        expected_extras,
        _show_document,
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

        _show_document.assert_called_once_with(
            document_url=pyramid_request.parsed_params["document_url"],
            assignment_extra=expected_extras,
        )

    def test_configured_launch(
        self, svc, document_url_service, pyramid_request, _show_document
    ):
        svc.configured_launch()

        document_url_service.get_document_url.assert_called_once_with(pyramid_request)

        _show_document.assert_called_once_with(
            document_url=document_url_service.get_document_url.return_value
        )

    def test_unconfigured_launch(
        self, svc, BearerTokenSchema, context, pyramid_request
    ):
        pyramid_request.lti_params = {
            "oauth_nonce": "STRIPPED",
            "oauth_timestamp": "STRIPPED",
            "oauth_signature": "STRIPPED",
            "id_token": "STRIPPED",
            "other_values": "REMAIN",
        }

        svc.unconfigured_launch()

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        BearerTokenSchema.return_value.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        authorization = BearerTokenSchema.return_value.authorization_param.return_value

        context.js_config.enable_file_picker_mode.assert_called_once_with(
            form_action="http://example.com/assignment",
            form_fields={"other_values": "REMAIN", "authorization": authorization},
        )

    def test_unconfigured_launch_not_authorized(
        self, context, pyramid_request, has_permission
    ):
        has_permission.return_value = False

        response = BasicLaunchViews(context, pyramid_request).unconfigured_launch()

        has_permission.assert_called_once_with(Permissions.LTI_CONFIGURE_ASSIGNMENT)
        assert (
            pyramid_request.override_renderer
            == "lms:templates/lti/basic_launch/unconfigured_launch_not_authorized.html.jinja2"
        )
        assert not response

    @pytest.fixture
    def has_permission(self, pyramid_request):
        with patch.object(pyramid_request, "has_permission") as has_permission:
            yield has_permission

    def test__show_document(
        self,
        svc,
        pyramid_request,
        context,
        lti_h_service,
        assignment_service,
        lti_role_service,
        grouping_service,
    ):
        # pylint: disable=protected-access
        result = svc._show_document(
            sentinel.document_url, assignment_extra=sentinel.assignment_extra
        )

        lti_h_service.sync.assert_called_once_with(
            [context.course], pyramid_request.lti_params
        )

        # `_record_course()`
        grouping_service.upsert_grouping_memberships.assert_called_once_with(
            user=pyramid_request.user, groups=[context.course]
        )

        # `_record_assignment()`
        assignment_service.upsert_assignment.assert_called_once_with(
            tool_consumer_instance_guid=pyramid_request.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=pyramid_request.lti_params["resource_link_id"],
            document_url=sentinel.document_url,
            lti_params=pyramid_request.lti_params,
            is_gradable=False,
            extra=sentinel.assignment_extra,
        )
        assignment = assignment_service.upsert_assignment.return_value

        lti_role_service.get_roles.assert_called_once_with(
            pyramid_request.lti_params["roles"]
        )
        assignment_service.upsert_assignment_membership.assert_called_once_with(
            assignment=assignment,
            user=pyramid_request.user,
            lti_roles=lti_role_service.get_roles.return_value,
        )
        assignment_service.upsert_assignment_groupings.assert_called_once_with(
            assignment_id=assignment.id, groupings=[context.course]
        )

        context.js_config.enable_lti_launch_mode.assert_called_once_with(assignment)
        context.js_config.set_focused_user.assert_not_called()
        context.js_config.add_document_url.assert_called_once_with(
            sentinel.document_url
        )

        assert result == {}

    @pytest.mark.usefixtures("is_canvas")
    def test__show_document_focuses_on_users(self, svc, pyramid_request, context):
        pyramid_request.params["focused_user"] = sentinel.focused_user

        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.set_focused_user.assert_called_once_with(
            sentinel.focused_user
        )

    def test__show_document_focuses_on_users_only_for_canvas(
        self, svc, pyramid_request, context
    ):
        pyramid_request.params["focused_user"] = sentinel.focused_user

        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.set_focused_user.assert_not_called()

    @pytest.mark.usefixtures("with_gradable_assignment", "user_is_instructor")
    def test__show_document_enables_grading(self, svc, context):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.enable_grading_bar.assert_called()

    @pytest.mark.usefixtures("with_gradable_assignment", "user_is_learner")
    def test__show_document_does_not_enable_grading_for_students(self, svc, context):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.enable_grading_bar.assert_not_called()

    @pytest.mark.usefixtures("user_is_instructor")
    def test__show_document_does_not_enable_without_a_gradable_assignment(
        self, svc, context
    ):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.enable_grading_bar.assert_not_called()

    @pytest.mark.usefixtures(
        "with_gradable_assignment", "user_is_instructor", "is_canvas"
    )
    def test__show_document_does_not_enable_grading_for_canvas(self, svc, context):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.enable_grading_bar.assert_not_called()

    @pytest.mark.usefixtures(
        "with_gradable_assignment",
        "is_canvas",
        "with_student_grading_id",
        "user_is_learner",
    )
    def test__show_document_enables_speedgrader_settings(self, svc, context):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_called_once_with(
            sentinel.document_url
        )

    @pytest.mark.usefixtures("with_gradable_assignment", "with_student_grading_id")
    def test__show_document_no_speedgrader_without_canvas(self, svc, context):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.usefixtures(
        "is_canvas",
        "with_gradable_assignment",
        "with_student_grading_id",
        "user_is_instructor",
    )
    def test__show_document_no_speedgrader_with_instructor(self, svc, context):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.usefixtures("is_canvas", "with_student_grading_id")
    def test__show_document_no_speedgrader_without_gradable_assignment(
        self, svc, context
    ):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.usefixtures("with_gradable_assignment", "is_canvas")
    def test__show_document_no_speedgrader_without_grading_id(self, svc, context):
        svc._show_document(sentinel.document_url)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.fixture
    def with_gradable_assignment(self, pyramid_request):
        # This shows the assignment itself is gradable
        pyramid_request.lti_params["lis_outcome_service_url"] = "http://example.com"

    @pytest.fixture
    def with_student_grading_id(self, pyramid_request):
        # This shows that a student has launched the assignment and a grade
        # is assignable to them
        pyramid_request.lti_params["lis_result_sourcedid"] = "9083745892345834h5"

    @pytest.fixture
    def svc(self, context, pyramid_request):
        return BasicLaunchViews(context, pyramid_request)

    @pytest.fixture
    def _show_document(self, svc):
        with mock.patch.object(svc, "_show_document") as _show_document:
            yield _show_document

    @pytest.fixture
    def is_canvas(self, context):
        """Set the LMS that launched us to Canvas."""
        context.is_canvas = True

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_params = LTIParams.from_request(pyramid_request)

        return pyramid_request

    @pytest.fixture
    def context(self):
        context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)
        context.is_canvas = False
        return context

    @pytest.fixture
    def LtiLaunches(self, patch):
        return patch("lms.views.lti.basic_launch.LtiLaunches")

    @pytest.fixture(autouse=True)
    def BearerTokenSchema(self, patch):
        return patch("lms.views.lti.basic_launch.BearerTokenSchema")
