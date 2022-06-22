from unittest.mock import Mock, sentinel

import pytest

from lms.models import Grouping
from lms.services.exceptions import ExternalRequestError
from lms.services.grouping._plugin import GroupError
from lms.services.grouping._plugin.blackboard import BlackboardGroupingPlugin
from tests import factories


class TestBlackboardGroupingPlugin:
    def test_get_groups_for_learner(
        self, blackboard_api_client, plugin, grouping_service, course
    ):
        api_groups = plugin.get_groups_for_learner(
            grouping_service, course, sentinel.group_set_id
        )

        blackboard_api_client.course_groups.assert_called_once_with(
            course.lms_id, sentinel.group_set_id, current_student_own_groups_only=True
        )
        assert api_groups == blackboard_api_client.course_groups.return_value

    def test_get_groups_for_learner_when_no_groups(
        self, blackboard_api_client, plugin, grouping_service, course
    ):
        blackboard_api_client.course_groups.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )
        assert (
            err.value.error_code
            == GroupError.ErrorCodes.BLACKBOARD_STUDENT_NOT_IN_GROUP
        )

    def test_get_groups_for_grading(self, plugin, grouping_service, course):
        api_groups = plugin.get_groups_for_grading(
            grouping_service, course, sentinel.group_set_id, sentinel.grading_student_id
        )

        grouping_service.get_course_groupings_for_user.assert_called_once_with(
            course,
            sentinel.grading_student_id,
            type_=Grouping.Type.BLACKBOARD_GROUP,
            group_set_id=sentinel.group_set_id,
        )
        assert api_groups == grouping_service.get_course_groupings_for_user.return_value

    def test_get_groups_for_instructor(
        self, blackboard_api_client, plugin, grouping_service, course
    ):
        api_groups = plugin.get_groups_for_instructor(
            grouping_service, course, sentinel.group_set_id
        )

        blackboard_api_client.group_set_groups.assert_called_once_with(
            course.lms_id, sentinel.group_set_id
        )
        assert api_groups == blackboard_api_client.group_set_groups.return_value

    def test_get_groups_for_instructor_raises(
        self, blackboard_api_client, plugin, grouping_service, course
    ):
        blackboard_api_client.group_set_groups.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )

    def test_get_groups_for_instructor_group_set_not_found(
        self, blackboard_api_client, plugin, grouping_service, course
    ):
        blackboard_api_client.group_set_groups.side_effect = ExternalRequestError(
            response=Mock(status_code=404)
        )

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )
        assert (
            err.value.error_code == GroupError.ErrorCodes.BLACKBOARD_GROUP_SET_NOT_FOUND
        )

    def test_get_groups_for_instructor_group_set_empty(
        self, blackboard_api_client, plugin, grouping_service, course
    ):
        blackboard_api_client.group_set_groups.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == GroupError.ErrorCodes.BLACKBOARD_GROUP_SET_EMPTY

    @pytest.fixture
    def plugin(self, blackboard_api_client):
        return BlackboardGroupingPlugin(blackboard_api_client)

    @pytest.fixture
    def course(self):
        return factories.Course()
