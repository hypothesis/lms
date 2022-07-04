from unittest.mock import sentinel

import pytest

from lms.views.api.sync import sync
from tests import factories
from tests.conftest import TEST_SETTINGS


@pytest.mark.usefixtures("application_instance_service")
class TestSync:
    @pytest.mark.parametrize(
        "grouping_method,extra_args",
        (("get_groups", {"group_set_id": sentinel.group_set_id}), ("get_sections", {})),
    )
    def test_it(
        self,
        pyramid_request,
        grouping_service,
        assignment_service,
        course_service,
        lti_h_service,
        grouping_method,
        extra_args,
    ):
        pyramid_request.parsed_params.update(extra_args)
        grouping_method = getattr(grouping_service, grouping_method)

        returned_ids = sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        grouping_method.assert_called_once_with(
            user=pyramid_request.user,
            lti_user=pyramid_request.lti_user,
            course=course_service.get_by_context_id.return_value,
            grading_student_id=sentinel.grading_student_id,
            **extra_args,
        )
        lti_h_service.sync.assert_called_once_with(
            grouping_method.return_value, sentinel.group_info
        )
        assignment_service.upsert_assignment_groupings(
            assignment_id=sentinel.assignment_id,
            groupings=grouping_method.return_value,
        )

        assert returned_ids == [
            group.groupid(TEST_SETTINGS["h_authority"])
            for group in grouping_method.return_value
        ]

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
            "assignment_id": sentinel.assignment_id,
            "lms": {"tool_consumer_instance_guid": sentinel.guid},
            "context_id": sentinel.context_id,
            "gradingStudentId": sentinel.grading_student_id,
            "group_info": sentinel.group_info,
        }
        pyramid_request.user = sentinel.user
        return pyramid_request
