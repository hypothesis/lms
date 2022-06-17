from unittest.mock import sentinel

import pytest

from lms.models import Grouping
from lms.services import CanvasAPIError
from lms.services.grouping._plugin.canvas import CanvasGroupingPlugin
from lms.services.grouping._plugin.exceptions import GroupError
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


class TestCanvasGroupingPlugin:
    def test_get_sections_for_learner(
        self, canvas_api_client, course, grouping_service, plugin
    ):
        api_groups = plugin.get_sections_for_learner(grouping_service, course)

        canvas_api_client.authenticated_users_sections.assert_called_once_with(
            sentinel.canvas_course_id
        )
        assert api_groups == canvas_api_client.authenticated_users_sections.return_value

    def test_get_sections_for_instructor(
        self, canvas_api_client, course, grouping_service, plugin
    ):
        api_groups = plugin.get_sections_for_instructor(grouping_service, course)

        canvas_api_client.course_sections.assert_called_once_with(
            sentinel.canvas_course_id
        )
        assert api_groups == canvas_api_client.course_sections.return_value

    def test_get_sections_for_grading(
        self, canvas_api_client, course, grouping_service, plugin
    ):
        canvas_api_client.users_sections.return_value = [
            {"id": canvas_api_client.course_sections.return_value}
        ]

        api_groups = plugin.get_sections_for_grading(grouping_service, course)

        canvas_api_client.course_sections.assert_called_once_with(
            sentinel.canvas_course_id
        )
        canvas_api_client.users_sections.assert_called_once_with(
            sentinel.grading_student_id, sentinel.canvas_course_id
        )
        assert groupings == grouping_service.upsert_groupings.return_value

    def test_get_groups_for_learner(
        self, canvas_api_client, grouping_service, plugin, course
    ):
        groups = [{"name": "group", "id": 1, "group_category_id": 2}]
        canvas_api_client.current_user_groups.return_value = groups
        group_set_id = 1

        api_groups = plugin.get_groups_for_learner(
            grouping_service, course, group_set_id
        )

        canvas_api_client.current_user_groups.assert_called_once_with(
            sentinel.canvas_course_id, group_set_id
        )

    def test_get_groups_for_learner_not_in_group(
        self, grouping_service, canvas_api_client, course, plugin
    ):
        # pylint: disable=protected-access
        canvas_api_client.current_user_groups.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )

        assert 1 == 2

    def test_get_groups_for_grading(
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
    def test_get_groups_for_instructor(
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

    @pytest.fixture
    def course(self):
        return factories.Course(
            extra={"canvas": {"custom_canvas_course_id": sentinel.canvas_course_id}}
        )

    @pytest.fixture
    def plugin(self, canvas_api_client):
        return CanvasGroupingPlugin(canvas_api_client)
