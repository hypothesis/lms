from unittest import mock
from unittest.mock import patch, sentinel

import pytest

from lms.models import LTIParams
from lms.product import Product
from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.security import Permissions
from lms.views.lti.basic_launch import BasicLaunchViews
from tests import factories


@pytest.mark.usefixtures(
    "assignment_service",
    "course_service",
    "application_instance_service",
    "grading_info_service",
    "lti_h_service",
    "lti_role_service",
    "grouping_service",
)
class TestBasicLaunchViews:
    def test___init___(
        self, context, pyramid_request, grouping_service, course_service
    ):
        BasicLaunchViews(context, pyramid_request)

        # `_record_course()`
        course_service.get_from_launch.assert_called_once_with(
            pyramid_request.product, pyramid_request.lti_params
        )
        grouping_service.upsert_grouping_memberships.assert_called_once_with(
            user=pyramid_request.user,
            groups=[course_service.get_from_launch.return_value],
        )

        # `_record_launch()`
        pyramid_request.lti_user.application_instance.check_guid_aligns.assert_called_once_with(
            pyramid_request.lti_params["tool_consumer_instance_guid"]
        )

    @pytest.mark.usefixtures("user_is_learner")
    def test__init__stores_data(
        self,
        context,
        pyramid_request,
        grading_info_service,
        application_instance_service,
        lti_user,
    ):
        BasicLaunchViews(context, pyramid_request)

        application_instance_service.update_from_lti_params.assert_called_once_with(
            lti_user.application_instance, pyramid_request.lti_params
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

    @pytest.mark.usefixtures("user_is_learner", "with_canvas")
    def test__init___doesnt_update_grading_info_for_canvas(
        self, context, pyramid_request, grading_info_service
    ):
        BasicLaunchViews(context, pyramid_request)

        grading_info_service.upsert_from_request.assert_not_called()

    def test_configure_assignment_callback(
        self, svc, pyramid_request, _show_document, assignment_service
    ):
        pyramid_request.parsed_params = {
            "document_url": sentinel.document_url,
            "group_set": sentinel.group_set,
        }

        svc.configure_assignment_callback()

        assignment_service.create_assignment.assert_called_once_with(
            tool_consumer_instance_guid="TEST_TOOL_CONSUMER_INSTANCE_GUID",
            resource_link_id="TEST_RESOURCE_LINK_ID",
        )
        assignment_service.update_assignment.assert_called_once_with(
            pyramid_request,
            assignment_service.create_assignment.return_value,
            document_url=sentinel.document_url,
            group_set_id=sentinel.group_set,
        )
        _show_document.assert_called_once_with(
            assignment_service.create_assignment.return_value,
        )

    def test_edit_assignment_callback(
        self,
        svc,
        pyramid_request,
        _show_document,
        assignment_service,
        LTIEvent,
    ):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "group_set": sentinel.group_set,
        }

        svc.edit_assignment_callback()

        assignment_service.get_assignment.assert_called_once_with(
            tool_consumer_instance_guid="TEST_TOOL_CONSUMER_INSTANCE_GUID",
            resource_link_id="TEST_RESOURCE_LINK_ID",
        )
        assignment = assignment_service.get_assignment.return_value
        LTIEvent.assert_called_once_with(
            request=pyramid_request,
            type=LTIEvent.Type.EDITED_ASSIGNMENT,
            data={
                "old_url": assignment.document_url,
                "old_group_set_id": assignment.extra.get.return_value,
            },
        )
        pyramid_request.registry.notify.has_call_with(LTIEvent.return_value)
        _show_document.assert_called_once_with(
            assignment_service.get_assignment.return_value,
        )

    def test_lti_launch_configured(
        self,
        svc,
        assignment_service,
        pyramid_request,
        _show_document,
        LTIEvent,
    ):
        svc.lti_launch()

        assignment_service.get_assignment_for_launch.assert_called_once_with(
            pyramid_request
        )

        _show_document.assert_called_once_with(
            assignment_service.get_assignment_for_launch.return_value
        )
        LTIEvent.assert_called_once_with(
            request=pyramid_request,
            type=LTIEvent.Type.CONFIGURED_LAUNCH,
        )
        pyramid_request.registry.notify.has_call_with(LTIEvent.return_value)

    def test_lti_launch_unconfigured(
        self, svc, context, pyramid_request, assignment_service
    ):
        assignment_service.get_assignment_for_launch.return_value = None

        pyramid_request.lti_params = mock.create_autospec(
            LTIParams, spec_set=True, instance=True
        )

        svc.lti_launch()

        pyramid_request.lti_params.serialize.assert_called_once_with(
            authorization=context.js_config.auth_token
        )
        context.js_config.enable_file_picker_mode.assert_called_once_with(
            form_action="http://example.com/assignment",
            form_fields=pyramid_request.lti_params.serialize.return_value,
        )

    def test_lti_launch_unconfigured_launch_not_authorized(
        self, context, pyramid_request, has_permission, assignment_service
    ):
        has_permission.return_value = False
        assignment_service.get_assignment_for_launch.return_value = None

        response = BasicLaunchViews(context, pyramid_request).lti_launch()

        has_permission.assert_called_once_with(Permissions.LTI_CONFIGURE_ASSIGNMENT)
        assert (
            pyramid_request.override_renderer
            == "lms:templates/lti/basic_launch/unconfigured_launch_not_authorized.html.jinja2"
        )
        assert not response

    def test_reconfigure_assignment_config(
        self, svc, context, pyramid_request, assignment_service
    ):
        pyramid_request.lti_params = mock.create_autospec(
            LTIParams, spec_set=True, instance=True
        )

        response = svc.reconfigure_assignment_config()

        assignment = assignment_service.get_assignment.return_value
        pyramid_request.lti_params.serialize.assert_called_once_with(
            authorization=context.js_config.auth_token
        )
        context.js_config.enable_file_picker_mode.assert_called_once_with(
            form_action="http://example.com/assignment/edit",
            form_fields=pyramid_request.lti_params.serialize.return_value,
        )
        assert response == {
            "assignment": {
                "group_set_id": assignment.extra.get.return_value,
                "document": {"url": assignment.document_url},
            },
            "filePicker": context.js_config.enable_file_picker_mode.return_value[
                "filePicker"
            ],
        }

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
        lti_user,
        course_service,
        assignment,
    ):
        # pylint: disable=protected-access
        result = svc._show_document(assignment)

        lti_h_service.sync.assert_called_once_with(
            [course_service.get_from_launch.return_value], pyramid_request.lti_params
        )

        # `_record_assignment()`
        assignment_service.upsert_assignment_membership.assert_called_once_with(
            assignment=assignment,
            user=pyramid_request.user,
            lti_roles=lti_user.lti_roles,
        )
        assignment_service.upsert_assignment_groupings.assert_called_once_with(
            assignment, groupings=[course_service.get_from_launch.return_value]
        )

        context.js_config.enable_lti_launch_mode.assert_called_once_with(
            course_service.get_from_launch.return_value, assignment
        )
        context.js_config.set_focused_user.assert_not_called()
        context.js_config.add_document_url.assert_called_once_with(
            assignment.document_url
        )

        assert result == {}

    @pytest.mark.usefixtures("with_canvas")
    def test__show_document_focuses_on_users(
        self, svc, pyramid_request, context, assignment
    ):
        pyramid_request.params["focused_user"] = sentinel.focused_user

        svc._show_document(assignment)  # pylint: disable=protected-access

        context.js_config.set_focused_user.assert_called_once_with(
            sentinel.focused_user
        )

    def test__show_document_focuses_on_users_only_for_canvas(
        self, svc, pyramid_request, context, assignment
    ):
        pyramid_request.params["focused_user"] = sentinel.focused_user

        svc._show_document(assignment)  # pylint: disable=protected-access

        context.js_config.set_focused_user.assert_not_called()

    @pytest.mark.usefixtures("user_is_instructor")
    @pytest.mark.parametrize("is_gradable", [True, False])
    def test__show_document_enables_instructor_toolbar_for_instructors(
        self, svc, context, is_gradable
    ):
        assignment = factories.Assignment(is_gradable=is_gradable)

        svc._show_document(assignment)  # pylint: disable=protected-access

        context.js_config.enable_instructor_toolbar.assert_called_with(
            enable_grading=is_gradable
        )

    @pytest.mark.usefixtures("user_is_learner")
    def test__show_document_does_not_enable_instructor_toolbar_for_students(
        self, svc, context, gradable_assignment
    ):
        svc._show_document(gradable_assignment)  # pylint: disable=protected-access

        context.js_config.enable_instructor_toolbar.assert_not_called()

    @pytest.mark.usefixtures("user_is_instructor", "with_canvas")
    def test__show_document_does_not_enable_instructor_toolbar_in_canvas(
        self,
        svc,
        context,
        application_instance,
        gradable_assignment,
    ):
        application_instance.settings.set(
            "hypothesis", "edit_assignments_enabled", True
        )

        svc._show_document(gradable_assignment)  # pylint: disable=protected-access

        context.js_config.enable_instructor_toolbar.assert_not_called()

    @pytest.mark.usefixtures(
        "with_canvas",
        "with_student_grading_id",
        "user_is_learner",
    )
    def test__show_document_enables_speedgrader_settings(
        self, svc, context, gradable_assignment
    ):
        svc._show_document(gradable_assignment)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_called_once_with(
            gradable_assignment.document_url
        )

    @pytest.mark.usefixtures("with_student_grading_id")
    def test__show_document_no_speedgrader_without_canvas(
        self, svc, context, gradable_assignment
    ):
        svc._show_document(gradable_assignment)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.usefixtures(
        "with_canvas", "with_student_grading_id", "user_is_instructor"
    )
    def test__show_document_no_speedgrader_with_instructor(
        self, svc, context, gradable_assignment
    ):
        svc._show_document(gradable_assignment)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.usefixtures("with_canvas", "with_student_grading_id")
    def test__show_document_no_speedgrader_without_gradable_assignment(
        self, svc, context, assignment
    ):
        svc._show_document(assignment)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.usefixtures("with_canvas")
    def test__show_document_no_speedgrader_without_grading_id(
        self, svc, context, gradable_assignment
    ):
        svc._show_document(gradable_assignment)  # pylint: disable=protected-access

        context.js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.fixture
    def gradable_assignment(self):
        return factories.Assignment(is_gradable=True)

    @pytest.fixture
    def assignment(self):
        return factories.Assignment(is_gradable=False)

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
    def with_canvas(self, pyramid_request):
        pyramid_request.product.family = Product.Family.CANVAS

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = factories.User()
        pyramid_request.lti_params = LTIParams.from_request(pyramid_request)

        return pyramid_request

    @pytest.fixture
    def context(self, application_instance):
        context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)

        application_instance.check_guid_aligns = mock.Mock()
        return context

    @pytest.fixture
    def LTIEvent(self, patch):
        return patch("lms.views.lti.basic_launch.LTIEvent")
