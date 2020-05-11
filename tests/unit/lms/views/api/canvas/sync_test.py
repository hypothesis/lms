import pytest

from lms.views.api.canvas.sync import sync
from tests import factories


def test_sync_when_the_user_is_a_learner(
    pyramid_request, canvas_api_client, lti_h_service
):
    pyramid_request.lti_user = pyramid_request.lti_user._replace(roles="Learner")

    returned_groupids = sync(pyramid_request)

    expected_groups = [
        factories.HGroup(
            name="Section 2",
            authority_provided_id="d99674b9700f4a40a2b301d2949b61339c58236c",
            type="section_group",
        )
    ]
    canvas_api_client.authenticated_users_sections.assert_called_once_with(
        "test_custom_canvas_course_id"
    )
    assert_that_it_called_sync_and_returned_the_groupids(
        lti_h_service, returned_groupids, expected_groups
    )


def test_sync_when_the_user_isnt_a_learner(
    pyramid_request, canvas_api_client, lti_h_service
):
    pyramid_request.lti_user = pyramid_request.lti_user._replace(roles="Instructor")

    returned_groupids = sync(pyramid_request)

    expected_groups = [
        factories.HGroup(
            name="Section 1",
            authority_provided_id="d0f36006728f2277f228b74c8a7f620305bfb3e7",
            type="section_group",
        ),
        factories.HGroup(
            name="Section 2",
            authority_provided_id="d99674b9700f4a40a2b301d2949b61339c58236c",
            type="section_group",
        ),
        factories.HGroup(
            name="Section 3",
            authority_provided_id="6a85e3651705dee4da0805b8985472343cbea94e",
            type="section_group",
        ),
    ]
    canvas_api_client.course_sections.assert_called_once_with(
        "test_custom_canvas_course_id"
    )
    assert_that_it_called_sync_and_returned_the_groupids(
        lti_h_service, returned_groupids, expected_groups
    )


def test_sync_when_in_SpeedGrader(pyramid_request, canvas_api_client, lti_h_service):
    pyramid_request.lti_user = pyramid_request.lti_user._replace(roles="Instructor")
    pyramid_request.json["learner"] = {
        "canvas_user_id": "test_canvas_user_id",
    }

    returned_groupids = sync(pyramid_request)

    instructors_groups = [
        factories.HGroup(
            name="Section 1",
            authority_provided_id="d0f36006728f2277f228b74c8a7f620305bfb3e7",
            type="section_group",
        ),
        factories.HGroup(
            name="Section 2",
            authority_provided_id="d99674b9700f4a40a2b301d2949b61339c58236c",
            type="section_group",
        ),
        factories.HGroup(
            name="Section 3",
            authority_provided_id="6a85e3651705dee4da0805b8985472343cbea94e",
            type="section_group",
        ),
    ]
    canvas_api_client.course_sections.assert_called_once_with(
        "test_custom_canvas_course_id"
    )
    lti_h_service.sync.assert_called_once_with(instructors_groups, {"foo": "bar"})
    canvas_api_client.users_sections.assert_called_once_with(
        "test_canvas_user_id", "test_custom_canvas_course_id"
    )
    assert returned_groupids == [
        "group:d99674b9700f4a40a2b301d2949b61339c58236c@TEST_AUTHORITY"
    ]


def assert_that_it_called_sync_and_returned_the_groupids(
    lti_h_service, returned_groupids, expected_groups
):
    lti_h_service.sync.assert_called_once_with(expected_groups, {"foo": "bar"})
    assert returned_groupids == [
        f"group:{group.authority_provided_id}@TEST_AUTHORITY"
        for group in expected_groups
    ]


pytestmark = pytest.mark.usefixtures("canvas_api_client", "lti_h_service")


@pytest.fixture
def canvas_api_client(canvas_api_client):
    # The course has three sections named "Section 1", "Section 2" and "Section
    # 3" (with IDs 1, 2 and 3).
    canvas_api_client.course_sections.return_value = [
        {"id": i, "name": f"Section {i}",} for i in range(1, 4)
    ]

    # The learner is only a member of section 2.
    canvas_api_client.authenticated_users_sections.return_value = [
        {"id": 2, "name": "Section 2"}
    ]

    # users_sections() returns id's only, not names.
    canvas_api_client.users_sections.return_value = [{"id": 2}]

    return canvas_api_client


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.json = {
        "course": {
            "context_id": "test_context_id",
            "custom_canvas_course_id": "test_custom_canvas_course_id",
        },
        "lms": {"tool_consumer_instance_guid": "test_tool_consumer_instance_guid"},
        "group_info": {"foo": "bar"},
    }
    return pyramid_request
