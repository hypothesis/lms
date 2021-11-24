import pytest

from lms.models import Grouping
from lms.views.api.blackboard.sync import Sync
from tests.conftest import TEST_SETTINGS

pytestmark = pytest.mark.usefixtures(
    "assignment_service",
    "lti_h_service",
    "grouping_service",
    "course_service",
    "blackboard_api_client",
)


def test_it(pyramid_request, assert_sync_and_return_groups, blackboard_api_client):
    groups = [{"name": "GROUP", "id": "1", "groupSetId": "2"}]
    blackboard_api_client.group_set_groups.return_value = groups

    result = Sync(pyramid_request).sync()

    assert_sync_and_return_groups(result, groups=groups)


@pytest.fixture
def assert_sync_and_return_groups(
    lti_h_service, request_json, grouping_service, course_service
):
    tool_guid = request_json["lms"]["tool_consumer_instance_guid"]

    def assert_return_values(groupids, groups):
        expected_groups = [
            grouping_service.upsert_with_parent(
                tool_consumer_instance_guid=tool_guid,
                lms_id=group["id"],
                lms_name=group.get("name", f"Group {group['id']}"),
                parent=course_service.get.return_value,
                type_=Grouping.Type.CANVAS_GROUP,
                extra={"group_set_id": group["groupSetId"]},
            )
            for group in groups
        ]

        lti_h_service.sync.assert_called_once_with(
            expected_groups, request_json["group_info"]
        )

        assert groupids == [
            group.groupid(TEST_SETTINGS["h_authority"]) for group in expected_groups
        ]

    return assert_return_values


@pytest.fixture
def request_json():
    return {
        "course": {
            "context_id": "test_context_id",
        },
        "assignment": {
            "resource_link_id": "test_resource_link_id",
        },
        "lms": {"tool_consumer_instance_guid": "test_tool_consumer_instance_guid"},
        "group_info": {"foo": "bar"},
    }


@pytest.fixture
def pyramid_request(pyramid_request, request_json):
    pyramid_request.json = request_json
    return pyramid_request
