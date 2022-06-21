from unittest.mock import sentinel

import pytest

from lms.models import Grouping
from lms.services import CanvasAPIError
from lms.services.grouping._plugin.canvas import CanvasGroupingPlugin
from lms.services.grouping._plugin.exceptions import GroupError
from tests import factories


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

        api_groups = plugin.get_sections_for_grading(
            grouping_service, course, sentinel.grading_student_id
        )

        canvas_api_client.course_sections.assert_called_once_with(
            sentinel.canvas_course_id
        )
        canvas_api_client.users_sections.assert_called_once_with(
            sentinel.grading_student_id, sentinel.canvas_course_id
        )
        assert "TODO" == "assert result sections"

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

        assert err.value.error_code == GroupError.ErrorCodes.CANVAS_STUDENT_NOT_IN_GROUP

    def test_get_groups_for_instructor(
        self, canvas_api_client, grouping_service, plugin, course
    ):
        api_groups = plugin.get_groups_for_instructor(
            grouping_service, course, sentinel.group_set_id
        )

        canvas_api_client.group_category_groups.assert_called_once_with(
            sentinel.group_set_id
        )
        assert canvas_api_client.group_category_groups.return_value == api_groups

    @pytest.fixture
    def course(self):
        return factories.Course(
            extra={"canvas": {"custom_canvas_course_id": sentinel.canvas_course_id}}
        )

    @pytest.fixture
    def plugin(self, canvas_api_client):
        return CanvasGroupingPlugin(canvas_api_client)
