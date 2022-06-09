from unittest.mock import sentinel

import pytest

from lms.models import Grouping
from lms.services import CanvasAPIError
from lms.services.product.grouping._canvas import CanvasGroupingService
from lms.views import (
    CanvasGroupSetEmpty,
    CanvasGroupSetNotFound,
    CanvasStudentNotInGroup,
)
from tests import factories
from tests.conftest import TEST_SETTINGS

pytestmark = pytest.mark.usefixtures(
    "canvas_api_client",
    "lti_h_service",
    "grouping_service",
    "course_service",
    "application_instance_service",
    "user_service",
)


@pytest.mark.usefixtures("user_is_learner")
def test_get_sections_when_the_user_is_a_learner(
    canvas_api_client, course, grouping_service, svc, user
):
    groupings = svc.get_sections(course)

    canvas_api_client.authenticated_users_sections.assert_called_once_with(
        sentinel.canvas_course_id
    )
    grouping_service.upsert_groupings.assert_called_once_with(
        canvas_api_client.authenticated_users_sections.return_value,
        parent=course,
        type_=Grouping.Type.CANVAS_SECTION,
    )
    grouping_service.upsert_grouping_memberships.assert_called_once_with(
        user, grouping_service.upsert_groupings.return_value
    )
    assert groupings == grouping_service.upsert_groupings.return_value


@pytest.mark.usefixtures("user_is_instructor")
def test_sections_when_the_user_is_an_instructor(
    canvas_api_client, course, grouping_service, svc, user
):
    groupings = svc.get_sections(course)

    canvas_api_client.course_sections.assert_called_once_with(sentinel.canvas_course_id)
    grouping_service.upsert_groupings.assert_called_once_with(
        canvas_api_client.course_sections.return_value,
        parent=course,
        type_=Grouping.Type.CANVAS_SECTION,
    )
    grouping_service.upsert_grouping_memberships.assert_called_once_with(
        user, grouping_service.upsert_groupings.return_value
    )
    assert groupings == grouping_service.upsert_groupings.return_value


@pytest.mark.usefixtures("user_is_instructor")
def test_sections_sync_when_in_SpeedGrader(
    canvas_api_client, course, grouping_service, svc, user
):
    canvas_api_client.users_sections.return_value = [
        {"id": canvas_api_client.course_sections.return_value}
    ]

    groupings = svc.get_sections(course, sentinel.grading_student_id)

    canvas_api_client.course_sections.assert_called_once_with(sentinel.canvas_course_id)
    canvas_api_client.users_sections.assert_called_once_with(
        sentinel.grading_student_id, sentinel.canvas_course_id
    )
    grouping_service.upsert_groupings.assert_called_once_with(
        canvas_api_client.course_sections.return_value,
        parent=course,
        type_=Grouping.Type.CANVAS_SECTION,
    )
    grouping_service.upsert_grouping_memberships.assert_called_once_with(
        user, grouping_service.upsert_groupings.return_value
    )
    assert groupings == grouping_service.upsert_groupings.return_value


@pytest.mark.usefixtures("user_is_learner", "is_group_launch")
def test_get_canvas_groups_learner(
    pyramid_request,
    canvas_api_client,
    assert_sync_and_return_groups,
    user_service,
    grouping_service,
):
    groups = [{"name": "group", "id": 1, "group_category_id": 2}]
    canvas_api_client.current_user_groups.return_value = groups
    group_set = 1
    course_id = "test_custom_canvas_course_id"

    groupids = Sync(pyramid_request).sync()

    canvas_api_client.current_user_groups.assert_called_once_with(course_id, group_set)
    grouping_service.upsert_grouping_memberships.assert_called_once_with(
        user_service.get.return_value,
        grouping_service.upsert_groupings.return_value,
    )

    assert_sync_and_return_groups(groupids, groups=groups)


@pytest.mark.usefixtures("user_is_learner", "is_group_launch")
def test_get_canvas_groups_learner_empty(pyramid_request, canvas_api_client):
    # pylint: disable=protected-access
    canvas_api_client.current_user_groups.return_value = []

    with pytest.raises(CanvasStudentNotInGroup):
        Sync(pyramid_request)._get_canvas_groups()


@pytest.mark.usefixtures("is_group_and_speedgrader", "user_is_instructor")
def test_get_canvas_groups_speedgrader(
    pyramid_request, canvas_api_client, assert_sync_and_return_groups
):
    groups = [{"name": "group", "id": 1, "group_category_id": 2}]
    canvas_api_client.user_groups.return_value = groups
    group_set = 1
    course_id = "test_custom_canvas_course_id"
    learner_id = 111

    groupids = Sync(pyramid_request).sync()

    canvas_api_client.user_groups.assert_called_once_with(
        course_id, learner_id, group_set
    )
    assert_sync_and_return_groups(groupids, groups=groups)


@pytest.mark.usefixtures("user_is_instructor", "is_group_launch")
def test_get_canvas_groups_instructor(
    pyramid_request, canvas_api_client, assert_sync_and_return_groups
):
    groups = [{"name": "group", "id": 1, "group_category_id": 2}]
    canvas_api_client.group_category_groups.return_value = groups
    group_set = 1

    groupids = Sync(pyramid_request).sync()

    canvas_api_client.group_category_groups.assert_called_once_with(group_set)
    assert_sync_and_return_groups(groupids, groups=groups)


@pytest.mark.usefixtures("user_is_instructor", "is_group_launch")
def test_get_canvas_groups_instructor_empty(pyramid_request, canvas_api_client):
    canvas_api_client.group_category_groups.return_value = []

    with pytest.raises(CanvasGroupSetEmpty):
        Sync(pyramid_request).sync()


@pytest.mark.usefixtures("user_is_instructor", "is_group_launch")
def test_get_canvas_groups_instructor_not_found_group_set(
    pyramid_request, canvas_api_client
):
    canvas_api_client.group_category_groups.side_effect = CanvasAPIError

    with pytest.raises(CanvasGroupSetNotFound):
        Sync(pyramid_request).sync()


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
    application_instance_service.get_current.return_value.settings = {
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
    application_instance_service.get_current.return_value.settings = {
        "canvas": {"groups_enabled": groups_enabled}
    }
    # pylint: disable=protected-access
    request_json["course"] = {"group_set": group_set_value}

    assert Sync(pyramid_request)._is_group_launch == expected_value


@pytest.fixture
def assert_sync_and_return_sections(
    lti_h_service, request_json, grouping_service, course_service
):
    def assert_return_values(groupids, sections):
        expected_groups = grouping_service.upsert_groupings(
            [
                {
                    "lms_id": section["id"],
                    "lms_name": section.get("name", f"Section {section['id']}"),
                }
                for section in sections
            ],
            parent=course_service.get_by_context_id.return_value,
            type_=Grouping.Type.CANVAS_SECTION,
        )

        lti_h_service.sync.assert_called_once_with(
            expected_groups, request_json["group_info"]
        )

        assert groupids == [
            group.groupid(TEST_SETTINGS["h_authority"]) for group in expected_groups
        ]

    return assert_return_values


@pytest.fixture
def assert_sync_and_return_groups(
    lti_h_service, request_json, grouping_service, course_service
):
    def assert_return_values(groupids, groups):
        expected_groups = grouping_service.upsert_groupings(
            [
                {
                    "lms_id": group["id"],
                    "lms_name": group.get("name", f"Group {group['id']}"),
                    "extra": {"group_set_id": group["group_category_id"]},
                }
                for group in groups
            ],
            parent=course_service.get_by_context_id.return_value,
            type_=Grouping.Type.CANVAS_GROUP,
        )

        lti_h_service.sync.assert_called_once_with(
            expected_groups, request_json["group_info"]
        )

        assert groupids == [
            group.groupid(TEST_SETTINGS["h_authority"]) for group in expected_groups
        ]

    return assert_return_values


@pytest.fixture
def course():
    return factories.Course(
        extra={"canvas": {"custom_canvas_course_id": sentinel.canvas_course_id}}
    )


@pytest.fixture
def svc(grouping_service, canvas_api_client, lti_user, user):
    return CanvasGroupingService(user, lti_user, grouping_service, canvas_api_client)
