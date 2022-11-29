from unittest.mock import patch, sentinel

import pytest

from lms.services.lti_launch import LTILaunchService, factory


class TestLTILaunchService:
    def test_validate_launch(self, svc, pyramid_request):
        with patch.object(svc, "_application_instance", autospec=True) as ai:
            svc.validate_launch()

            ai.check_guid_aligns.assert_called_once_with(
                pyramid_request.lti_params["tool_consumer_instance_guid"]
            )

    def test_record_course(
        self, svc, launch_plugin, pyramid_request, grouping_service, course_service
    ):
        svc.record_course()

        course_service.upsert_course.assert_called_once_with(
            context_id=pyramid_request.lti_params["context_id"],
            name=pyramid_request.lti_params["context_title"],
            extra=launch_plugin.course_extra.return_value,
        )
        grouping_service.upsert_grouping_memberships.assert_called_once_with(
            user=pyramid_request.user,
            groups=[course_service.upsert_course.return_value],
        )

    def test_record_assignment(
        self, svc, assignment_service, pyramid_request, lti_role_service, launch_plugin
    ):

        svc.record_assignment(sentinel.course, sentinel.document_url, sentinel.extra)
        assignment_service.upsert_assignment.assert_called_once_with(
            document_url=sentinel.document_url,
            tool_consumer_instance_guid=pyramid_request.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=pyramid_request.lti_params["resource_link_id"],
            lti_params=pyramid_request.lti_params,
            extra=sentinel.extra,
            is_gradable=launch_plugin.is_assignment_gradable.return_value,
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
            assignment_id=assignment.id, groupings=[sentinel.course]
        )

    @pytest.mark.parametrize(
        "grading_bar,is_instructor,record_grading",
        [
            (True, True, False),
            (True, False, True),
            (False, True, False),
            (False, False, False),
        ],
    )
    def test_record_launch(
        self,
        svc,
        application_instance_service,
        application_instance,
        pyramid_request,
        grading_info_service,
        grading_bar,
        is_instructor,
        record_grading,
    ):
        pyramid_request.product.use_grading_bar = grading_bar
        svc.lti_user = pyramid_request.lti_user._replace(
            roles="Instructor" if is_instructor else "Learner"
        )

        svc.record_launch(pyramid_request)

        application_instance_service.update_from_lti_params(
            application_instance, pyramid_request.lti_params
        )

        if record_grading:
            grading_info_service.upsert_from_request.assert_called_once_with(
                pyramid_request
            )

    @pytest.fixture
    def svc(
        self,
        pyramid_request,
        course_service,
        assignment_service,
        grouping_service,
        lti_role_service,
        application_instance_service,
        grading_info_service,
        launch_plugin,
    ):
        return LTILaunchService(
            lti_params=pyramid_request.lti_params,
            user=pyramid_request.user,
            lti_user=pyramid_request.lti_user,
            course_service=course_service,
            assignment_service=assignment_service,
            grouping_service=grouping_service,
            lti_role_service=lti_role_service,
            application_instance_service=application_instance_service,
            grading_info_service=grading_info_service,
            product=pyramid_request.product,
            plugin=launch_plugin,
        )


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        LTILaunchService,
        course_service,
        assignment_service,
        grouping_service,
        lti_role_service,
        application_instance_service,
        grading_info_service,
        launch_plugin,
    ):
        service = factory(sentinel.context, pyramid_request)

        LTILaunchService.assert_called_once_with(
            lti_params=pyramid_request.lti_params,
            user=pyramid_request.user,
            lti_user=pyramid_request.lti_user,
            course_service=course_service,
            assignment_service=assignment_service,
            grouping_service=grouping_service,
            lti_role_service=lti_role_service,
            application_instance_service=application_instance_service,
            grading_info_service=grading_info_service,
            product=pyramid_request.product,
            plugin=launch_plugin,
        )
        assert service == LTILaunchService.return_value

    @pytest.fixture
    def LTILaunchService(self, patch):
        return patch("lms.services.lti_launch.LTILaunchService")
