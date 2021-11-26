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


@pytest.mark.usefixtures("user_is_instructor")
def test_it_when_instructor(
    pyramid_request, assert_sync_and_return_groups, blackboard_api_client, groups
):
    blackboard_api_client.group_set_groups.return_value = groups

    result = Sync(pyramid_request).sync()

    assert_sync_and_return_groups(result, groups=groups)


@pytest.mark.usefixtures(
    "user_is_learner", "user_service", "application_instance_service"
)
def test_it_when_student(
    pyramid_request,
    assert_sync_and_return_groups,
    blackboard_api_client,
    groups,
    grouping_service,
    user_service,
):
    blackboard_api_client.course_groups.return_value = groups

    result = Sync(pyramid_request).sync()

    assert_sync_and_return_groups(result, groups=groups)
    blackboard_api_client.course_groups.assert_called_once_with(
        pyramid_request.json["course"]["context_id"],
        "GROUP_SET_ID",
        current_student_own_groups_only=True,
    )
    grouping_service.upsert_grouping_memberships.assert_called_once_with(
        user_service.get.return_value,
        [grouping_service.upsert_with_parent.return_value for _ in groups],
    )


@pytest.fixture
def groups():
    return [{"name": "GROUP", "id": "1", "groupSetId": "2"}]


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


@pytest.fixture(autouse=True)
def assignment_service(assignment_service):
    assignment_service.get.return_value.extra = {"group_set_id": "GROUP_SET_ID"}
    return assignment_service


@pytest.fixture
def pyramid_request(pyramid_request, request_json):
    pyramid_request.json = request_json
    return pyramid_request
