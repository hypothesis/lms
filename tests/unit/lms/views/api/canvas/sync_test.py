from unittest import mock

import pytest

from lms.views.api.canvas.sync import Sync
from tests.conftest import TEST_SETTINGS

pytestmark = pytest.mark.usefixtures(
    "canvas_api_client",
    "lti_h_service",
    "grouping_service",
    "application_instance_service",
)


@pytest.mark.usefixtures("user_is_learner")
def test_sections_sync_when_the_user_is_a_learner(
    pyramid_request,
    canvas_api_client,
    sections,
    assert_sync_and_return_sections,
    request_json,
):
    groupids = Sync(pyramid_request).sync()

    course_id = request_json["course"]["custom_canvas_course_id"]
    canvas_api_client.authenticated_users_sections.assert_called_once_with(course_id)

    assert_sync_and_return_sections(groupids, sections=sections.authenticated_user)


@pytest.mark.usefixtures("is_group_launch")
def test_groups_sync(
    pyramid_request,
    assert_sync_and_return_groups,
):

    groups = [{"name": "group", "id": 1, "group_category_id": 2}]

    with mock.patch.object(
        Sync, "_get_canvas_groups", autospec=True
    ) as _get_canvas_groups:

        _get_canvas_groups.return_value = groups

        groupids = Sync(pyramid_request).sync()

    assert_sync_and_return_groups(groupids, groups=groups)


@pytest.mark.usefixtures("user_is_instructor")
def test_sections_sync_when_the_user_is_an_instructor(
    pyramid_request,
    canvas_api_client,
    sections,
    assert_sync_and_return_sections,
    request_json,
):
    groupids = Sync(pyramid_request).sync()

    course_id = request_json["course"]["custom_canvas_course_id"]
    canvas_api_client.course_sections.assert_called_once_with(course_id)

    assert_sync_and_return_sections(groupids, sections=sections.course)


@pytest.mark.usefixtures("user_is_learner", "is_group_launch")
def test_get_canvas_groups_learner(pyramid_request, canvas_api_client):
    # pylint: disable=protected-access
    group_set = 1
    course_id = "test_custom_canvas_course_id"

    Sync(pyramid_request)._get_canvas_groups()

    canvas_api_client.current_user_groups.assert_called_once_with(course_id, group_set)


@pytest.mark.usefixtures("is_group_and_speedgrader", "user_is_instructor")
def test_get_canvas_groups_speedgrader(pyramid_request, canvas_api_client):
    # pylint: disable=protected-access
    group_set = 1
    course_id = "test_custom_canvas_course_id"
    learner_id = 111

    Sync(pyramid_request)._get_canvas_groups()

    canvas_api_client.user_groups.assert_called_once_with(
        course_id, learner_id, group_set
    )


@pytest.mark.usefixtures("user_is_instructor", "is_group_launch")
def test_get_canvas_groups_instructor(pyramid_request, canvas_api_client):
    # pylint: disable=protected-access
    group_set = 1

    Sync(pyramid_request)._get_canvas_groups()

    canvas_api_client.group_category_groups.assert_called_once_with(group_set)


@pytest.mark.parametrize(
    "groups_enabled,group_set_value,expected_value",
    [
        (True, None, False),
        (True, "a", False),
        (True, "1", True),
        (True, 1, True),
        (False, "1", False),
    ],
)
def test_is_group_launch(
    groups_enabled,
    group_set_value,
    expected_value,
    pyramid_request,
    request_json,
    application_instance_service,
):
    application_instance_service.get.return_value.settings = {
        "canvas": {"groups_enabled": groups_enabled}
    }
    # pylint: disable=protected-access
    request_json["course"] = {"group_set": group_set_value}

    assert Sync(pyramid_request)._is_group_launch == expected_value


@pytest.mark.parametrize(
    "groups_enabled,group_set_value,expected_value",
    [
        (True, None, False),
        (True, "a", False),
        (True, "1", True),
        (True, 1, True),
        (False, 1, False),
    ],
)
def test_is_group_launch_in_speed_grader(
    groups_enabled,
    group_set_value,
    expected_value,
    pyramid_request,
    request_json,
    application_instance_service,
):
    application_instance_service.get.return_value.settings = {
        "canvas": {"groups_enabled": groups_enabled}
    }
    # pylint: disable=protected-access
    request_json["course"] = {"group_set": group_set_value}

    assert Sync(pyramid_request)._is_group_launch == expected_value


@pytest.mark.usefixtures("user_is_instructor")
@pytest.mark.usefixtures("is_speedgrader")
def test_sections_sync_when_in_SpeedGrader(
    pyramid_request,
    canvas_api_client,
    sections,
    assert_sync_and_return_sections,
    request_json,
):
    groupids = Sync(pyramid_request).sync()

    course_id = request_json["course"]["custom_canvas_course_id"]
    user_id = request_json["learner"]["canvas_user_id"]
    canvas_api_client.course_sections.assert_called_once_with(course_id)
    canvas_api_client.users_sections.assert_called_once_with(user_id, course_id)

    assert_sync_and_return_sections(groupids, sections=sections.user)


@pytest.fixture
def assert_sync_and_return_sections(lti_h_service, request_json, grouping_service):
    tool_guid = request_json["lms"]["tool_consumer_instance_guid"]
    context_id = request_json["course"]["context_id"]

    def assert_return_values(groupids, sections):
        expected_groups = [
            grouping_service.upsert_canvas_section(
                tool_consumer_instance_guid=tool_guid,
                context_id=context_id,
                section_id=section["id"],
                section_name=section.get("name", f"Section {section['id']}"),
            )
            for section in sections
        ]

        lti_h_service.sync.assert_called_once_with(
            expected_groups, request_json["group_info"]
        )

        assert groupids == [
            group.groupid(TEST_SETTINGS["h_authority"]) for group in expected_groups
        ]

    return assert_return_values


@pytest.fixture
def assert_sync_and_return_groups(lti_h_service, request_json, grouping_service):
    tool_guid = request_json["lms"]["tool_consumer_instance_guid"]
    context_id = request_json["course"]["context_id"]

    def assert_return_values(groupids, groups):
        expected_groups = [
            grouping_service.upsert_canvas_group(
                tool_consumer_instance_guid=tool_guid,
                context_id=context_id,
                group_id=group["id"],
                group_name=group.get("name", f"Group {group['id']}"),
                group_set_id=group["group_category_id"],
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
def sections():
    class Sections:
        # The course has three sections named "Section 1", "Section 2" and "Section
        # 3" (with IDs 1, 2 and 3).
        course = [{"id": i, "name": f"Section {i}"} for i in range(1, 4)]

        # users_sections() returns id's only, not names.
        authenticated_user = [{"id": 2, "name": "Section 2"}]

        # The learner is only a member of section 2.
        user = [{"id": section["id"]} for section in authenticated_user]

    return Sections()


@pytest.fixture
def canvas_api_client(canvas_api_client, sections):
    canvas_api_client.course_sections.return_value = sections.course
    canvas_api_client.authenticated_users_sections.return_value = (
        sections.authenticated_user
    )
    canvas_api_client.users_sections.return_value = sections.user

    return canvas_api_client


@pytest.fixture
def pyramid_request(pyramid_request, request_json):
    pyramid_request.json = request_json
    return pyramid_request


@pytest.fixture
def request_json():
    return {
        "course": {
            "context_id": "test_context_id",
            "custom_canvas_course_id": "test_custom_canvas_course_id",
        },
        "lms": {"tool_consumer_instance_guid": "test_tool_consumer_instance_guid"},
        "group_info": {"foo": "bar"},
    }


@pytest.fixture
def is_speedgrader(request_json):
    request_json["learner"] = {"canvas_user_id": 111}


@pytest.fixture
def is_group_launch(application_instance_service, request_json):
    request_json["course"]["group_set"] = 1
    application_instance_service.get.return_value.settings = {
        "canvas": {"groups_enabled": True}
    }


@pytest.fixture
def is_group_and_speedgrader(request_json):
    request_json["learner"] = {"canvas_user_id": 111, "group_set": 1}
