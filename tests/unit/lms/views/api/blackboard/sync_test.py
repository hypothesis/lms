from unittest.mock import sentinel

import pytest

from lms.views.api.blackboard.sync import Sync
from tests import factories
from tests.conftest import TEST_SETTINGS


@pytest.mark.usefixtures("application_instance_service", "lti_h_service")
class TestSync:
    def test_sync(
        self,
        lti_h_service,
        grouping_service,
        lti_user,
        course_service,
        pyramid_request,
        assignment_service,
    ):
        groups = factories.BlackboardGroup.create_batch(5)
        grouping_service.get_groups.return_value = groups

        groupids = Sync(pyramid_request).sync()

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        assignment_service.get_assignment.assert_called_once_with(
            sentinel.guid,
            sentinel.resource_link_id,
        )
        grouping_service.get_groups.assert_called_once_with(
            sentinel.user,
            lti_user,
            course_service.get_by_context_id.return_value,
            assignment_service.get_assignment.return_value.extra["group_set_id"],
            None,
        )
        lti_h_service.sync.assert_called_once_with(
            grouping_service.get_groups.return_value, sentinel.group_info
        )
        assert groupids == [
            group.groupid(TEST_SETTINGS["h_authority"]) for group in groups
        ]

    @pytest.fixture
    def pyramid_request(self, pyramid_request, request_json):
        pyramid_request.parsed_params = request_json
        pyramid_request.user = sentinel.user
        return pyramid_request

    @pytest.fixture
    def request_json(self):
        return {
            "course": {
                "context_id": sentinel.context_id,
                "custom_canvas_course_id": "test_custom_canvas_course_id",
            },
            "lms": {"tool_consumer_instance_guid": sentinel.guid},
            "assignment": {"resource_link_id": sentinel.resource_link_id},
            "group_info": sentinel.group_info,
        }
