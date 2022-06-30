from unittest.mock import sentinel

import pytest

from lms.views.api.sync import sync
from tests import factories
from tests.conftest import TEST_SETTINGS


@pytest.mark.usefixtures("application_instance_service", "lti_h_service")
class TestSync:
    def test_with_groups(
        self, lti_h_service, grouping_service, lti_user, course_service, pyramid_request
    ):
        groups = factories.BlackboardGroup.create_batch(5)
        grouping_service.get_groups.return_value = groups

        groupids = sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        grouping_service.get_groups.assert_called_once_with(
            sentinel.user,
            lti_user,
            course_service.get_by_context_id.return_value,
            sentinel.group_set_id,
            sentinel.grading_student_id,
        )
        lti_h_service.sync.assert_called_once_with(
            grouping_service.get_groups.return_value, sentinel.group_info
        )
        assert groupids == [
            group.groupid(TEST_SETTINGS["h_authority"]) for group in groups
        ]

    @pytest.mark.usefixtures("with_sections")
    def test_with_sections(
        self, lti_h_service, grouping_service, lti_user, course_service, pyramid_request
    ):
        sections = factories.CanvasSection.create_batch(5)
        grouping_service.get_sections.return_value = sections

        groupids = sync(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        grouping_service.get_sections.assert_called_once_with(
            sentinel.user,
            lti_user,
            course_service.get_by_context_id.return_value,
            sentinel.grading_student_id,
        )
        lti_h_service.sync.assert_called_once_with(
            grouping_service.get_sections.return_value, sentinel.group_info
        )
        assert groupids == [
            group.groupid(TEST_SETTINGS["h_authority"]) for group in sections
        ]

    @pytest.fixture
    def pyramid_request(self, pyramid_request, request_json):
        pyramid_request.parsed_params = request_json
        pyramid_request.user = sentinel.user
        return pyramid_request

    @pytest.fixture
    def request_json(self):
        return {
            "lms": {"tool_consumer_instance_guid": sentinel.guid},
            "context_id": sentinel.context_id,
            "group_set_id": sentinel.group_set_id,
            "gradingStudentId": sentinel.grading_student_id,
            "group_info": sentinel.group_info,
        }

    @pytest.fixture
    def with_sections(self, request_json):
        del request_json["group_set_id"]
