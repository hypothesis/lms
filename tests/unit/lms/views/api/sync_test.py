from unittest.mock import sentinel

import pytest

from lms.views.api.sync import sync
from tests import factories
from tests.conftest import TEST_SETTINGS


@pytest.mark.usefixtures("application_instance_service")
class TestSync:
    def test_with_groups(
        self, pyramid_request, grouping_service, course_service, assert_ids_returned
    ):
        pyramid_request.parsed_params["group_set_id"] = sentinel.group_set_id
        groupings = factories.BlackboardGroup.create_batch(5)
        grouping_service.get_groups.return_value = groupings

        returned_ids = sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        grouping_service.get_groups.assert_called_once_with(
            user=sentinel.user,
            lti_user=pyramid_request.lti_user,
            course=course_service.get_by_context_id.return_value,
            grading_student_id=sentinel.grading_student_id,
            group_set_id=sentinel.group_set_id,
        )
        assert_ids_returned(returned_ids, groupings)

    def test_with_sections(
        self, pyramid_request, grouping_service, course_service, assert_ids_returned
    ):
        groupings = factories.CanvasSection.create_batch(5)
        grouping_service.get_sections.return_value = groupings

        returned_ids = sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        grouping_service.get_sections.assert_called_once_with(
            user=sentinel.user,
            lti_user=pyramid_request.lti_user,
            course=course_service.get_by_context_id.return_value,
            grading_student_id=sentinel.grading_student_id,
        )
        assert_ids_returned(returned_ids, groupings)

    @pytest.fixture
    def assert_ids_returned(self, lti_h_service):
        # This name is a bit cheeky, as we are really testing everything which
        # is the same after the main if.
        def assert_ids_returned(returned_ids, groupings):
            lti_h_service.sync.assert_called_once_with(groupings, sentinel.group_info)

            assert returned_ids == [
                group.groupid(TEST_SETTINGS["h_authority"]) for group in groupings
            ]

        return assert_ids_returned

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "lms": {"tool_consumer_instance_guid": sentinel.guid},
            "context_id": sentinel.context_id,
            "gradingStudentId": sentinel.grading_student_id,
            "group_info": sentinel.group_info,
        }
        pyramid_request.user = sentinel.user
        return pyramid_request
