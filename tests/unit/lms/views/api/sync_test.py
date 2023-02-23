from unittest.mock import sentinel

import pytest

from lms.product.plugin.grouping import GroupError
from lms.views.api.sync import sync
from tests import factories
from tests.conftest import TEST_SETTINGS


@pytest.mark.usefixtures("application_instance_service")
class TestSync:
    def test_it_with_sections(
        self,
        pyramid_request,
        grouping_service,
        assignment_service,
        course_service,
        lti_h_service,
    ):
        returned_ids = sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(
            sentinel.context_id, raise_on_missing=True
        )
        course = course_service.get_by_context_id.return_value
        grouping_service.get_sections.assert_called_once_with(
            user=pyramid_request.user,
            lti_user=pyramid_request.lti_user,
            course=course_service.get_by_context_id.return_value,
            grading_student_id=sentinel.grading_student_id,
        )
        lti_h_service.sync.assert_called_once_with(
            grouping_service.get_sections.return_value, sentinel.group_info
        )
        assignment_service.get_assignment.assert_called_once_with(
            course.application_instance.tool_consumer_instance_guid,
            sentinel.resource_link_id,
        )
        assignment_service.upsert_assignment_groupings(
            assignment_service.get_assignment.return_value,
            groupings=grouping_service.get_groups.return_value,
        )

        assert returned_ids == [
            group.groupid(TEST_SETTINGS["h_authority"])
            for group in grouping_service.get_sections.return_value
        ]

    @pytest.mark.usefixtures("course_copy_plugin")
    def test_it_with_groups(
        self,
        pyramid_request,
        grouping_service,
        assignment_service,
        course_service,
        lti_h_service,
    ):
        pyramid_request.parsed_params["group_set_id"] = sentinel.group_set_id

        returned_ids = sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(
            sentinel.context_id, raise_on_missing=True
        )
        course = course_service.get_by_context_id.return_value
        course.get_mapped_group_set_id.assert_called_once_with(sentinel.group_set_id)
        grouping_service.get_groups.assert_called_once_with(
            user=pyramid_request.user,
            lti_user=pyramid_request.lti_user,
            course=course,
            grading_student_id=sentinel.grading_student_id,
            group_set_id=course.get_mapped_group_set_id.return_value,
        )
        lti_h_service.sync.assert_called_once_with(
            grouping_service.get_groups.return_value, sentinel.group_info
        )
        assignment_service.get_assignment.assert_called_once_with(
            course.application_instance.tool_consumer_instance_guid,
            sentinel.resource_link_id,
        )
        assignment_service.upsert_assignment_groupings(
            assignment_service.get_assignment.return_value,
            groupings=grouping_service.get_groups.return_value,
        )

        assert returned_ids == [
            group.groupid(TEST_SETTINGS["h_authority"])
            for group in grouping_service.get_groups.return_value
        ]

    @pytest.mark.usefixtures("course_copy_plugin")
    def test_it_with_groups_course_copy_fix(
        self,
        pyramid_request,
        grouping_service,
        course_service,
        course_copy_plugin,
        lti_h_service,
        assignment_service,
    ):
        pyramid_request.parsed_params["group_set_id"] = sentinel.group_set_id

        grouping_service.get_groups.side_effect = [
            GroupError(sentinel.error_code, sentinel.group_set),
            grouping_service.get_groups.return_value,
        ]
        course_copy_plugin.find_matching_group_set_in_course.return_value = (
            sentinel.new_group_set_id
        )

        returned_ids = sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(
            sentinel.context_id, raise_on_missing=True
        )
        course = course_service.get_by_context_id.return_value
        course.get_mapped_group_set_id.assert_called_once_with(sentinel.group_set_id)
        grouping_service.get_groups.assert_any_call(
            user=pyramid_request.user,
            lti_user=pyramid_request.lti_user,
            course=course,
            grading_student_id=sentinel.grading_student_id,
            group_set_id=course.get_mapped_group_set_id.return_value,
        )

        course_copy_plugin.find_matching_group_set_in_course.assert_called_once_with(
            course, course.get_mapped_group_set_id.return_value
        )

        grouping_service.get_groups.assert_called_with(
            user=pyramid_request.user,
            lti_user=pyramid_request.lti_user,
            course=course,
            grading_student_id=sentinel.grading_student_id,
            group_set_id=sentinel.new_group_set_id,
        )

        lti_h_service.sync.assert_called_once_with(
            grouping_service.get_groups.return_value, sentinel.group_info
        )
        assignment_service.get_assignment.assert_called_once_with(
            course.application_instance.tool_consumer_instance_guid,
            sentinel.resource_link_id,
        )
        assignment_service.upsert_assignment_groupings(
            assignment_service.get_assignment.return_value,
            groupings=grouping_service.get_groups.return_value,
        )

        assert returned_ids == [
            group.groupid(TEST_SETTINGS["h_authority"])
            for group in grouping_service.get_groups.return_value
        ]

    @pytest.mark.usefixtures("course_copy_plugin", "assignment_service")
    def test_it_with_groups_course_copy_doesnt_fix_it(
        self, pyramid_request, grouping_service, course_service, course_copy_plugin
    ):
        pyramid_request.parsed_params["group_set_id"] = sentinel.group_set_id

        grouping_service.get_groups.side_effect = GroupError(
            sentinel.error_code, sentinel.group_set
        )
        course_copy_plugin.find_matching_group_set_in_course.return_value = None

        with pytest.raises(GroupError):
            sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(
            sentinel.context_id, raise_on_missing=True
        )
        course = course_service.get_by_context_id.return_value
        course.get_mapped_group_set_id.assert_called_once_with(sentinel.group_set_id)
        grouping_service.get_groups.assert_called_once_with(
            user=pyramid_request.user,
            lti_user=pyramid_request.lti_user,
            course=course,
            grading_student_id=sentinel.grading_student_id,
            group_set_id=course.get_mapped_group_set_id.return_value,
        )

    @pytest.fixture
    def grouping_service(self, grouping_service):
        grouping_service.get_sections.return_value = (
            factories.CanvasSection.create_batch(3)
        )
        grouping_service.get_groups.return_value = (
            factories.BlackboardGroup.create_batch(3)
        )
        return grouping_service

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "resource_link_id": sentinel.resource_link_id,
            "lms": {"tool_consumer_instance_guid": sentinel.guid},
            "context_id": sentinel.context_id,
            "gradingStudentId": sentinel.grading_student_id,
            "group_info": sentinel.group_info,
        }
        pyramid_request.user = sentinel.user
        return pyramid_request
