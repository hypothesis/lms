import pytest

from lms.models import HGroup
from lms.views.api.canvas.sync import Sync
from tests.conftest import TEST_SETTINGS

pytestmark = pytest.mark.usefixtures("canvas_api_client", "lti_h_service")


@pytest.mark.usefixtures("is_learner")
def test_sync_when_the_user_is_a_learner(
    pyramid_request, canvas_api_client, sections, assert_sync_and_return, request_json
):
    groupids = Sync(pyramid_request).sync()

    course_id = request_json["course"]["custom_canvas_course_id"]
    canvas_api_client.authenticated_users_sections.assert_called_once_with(course_id)

    assert_sync_and_return(groupids, sections=sections.authenticated_user)


@pytest.mark.usefixtures("is_instructor")
def test_sync_when_the_user_is_an_instructor(
    pyramid_request, canvas_api_client, sections, assert_sync_and_return, request_json
):
    groupids = Sync(pyramid_request).sync()

    course_id = request_json["course"]["custom_canvas_course_id"]
    canvas_api_client.course_sections.assert_called_once_with(course_id)

    assert_sync_and_return(groupids, sections=sections.course)


@pytest.mark.usefixtures("is_instructor")
@pytest.mark.usefixtures("is_speedgrader")
def test_sync_when_in_SpeedGrader(
    pyramid_request, canvas_api_client, sections, assert_sync_and_return, request_json
):
    groupids = Sync(pyramid_request).sync()

    course_id = request_json["course"]["custom_canvas_course_id"]
    user_id = request_json["learner"]["canvas_user_id"]
    canvas_api_client.course_sections.assert_called_once_with(course_id)
    canvas_api_client.users_sections.assert_called_once_with(user_id, course_id)

    assert_sync_and_return(groupids, sections=sections.user)


@pytest.fixture
def assert_sync_and_return(lti_h_service, request_json):
    tool_guid = request_json["lms"]["tool_consumer_instance_guid"]
    context_id = request_json["course"]["context_id"]

    def assert_return_values(groupids, sections):
        expected_groups = [
            HGroup.section_group(
                section_name=section.get("name", f"Section {section['id']}"),
                tool_consumer_instance_guid=tool_guid,
                context_id=context_id,
                section_id=section["id"],
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
def is_instructor(pyramid_request):
    pyramid_request.lti_user = pyramid_request.lti_user._replace(roles="Instructor")


@pytest.fixture
def is_learner(pyramid_request):
    pyramid_request.lti_user = pyramid_request.lti_user._replace(roles="Learner")


@pytest.fixture
def is_speedgrader(request_json):
    request_json["learner"] = {"canvas_user_id": "user_id"}


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
