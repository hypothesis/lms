import random
from unittest.mock import Mock, patch, sentinel

import pytest

from lms.product.moodle._plugin.grouping import ErrorCodes, MoodleGroupingPlugin
from lms.product.plugin.grouping import GroupError
from lms.services.exceptions import ExternalRequestError
from tests import factories


class TestMoodleGroupingPlugin:
    def test_get_group_sets(self, plugin, moodle_api_client, course):
        api_group_sets = plugin.get_group_sets(course)

        moodle_api_client.course_group_sets.assert_called_once_with(course.lms_id)
        course.set_group_sets.assert_called_once_with(
            moodle_api_client.course_group_sets.return_value
        )
        assert api_group_sets == moodle_api_client.course_group_sets.return_value

    def test_get_groups_for_learner(
        self, moodle_api_client, plugin, grouping_service, course, lti_user
    ):
        api_groups = plugin.get_groups_for_learner(
            grouping_service, course, sentinel.group_set_id
        )

        moodle_api_client.groups_for_user.assert_called_once_with(
            course.lms_id, sentinel.group_set_id, lti_user.user_id
        )
        assert api_groups == moodle_api_client.groups_for_user.return_value

    def test_get_groups_for_learner_when_no_groups(
        self, moodle_api_client, plugin, grouping_service, course
    ):
        moodle_api_client.groups_for_user.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == ErrorCodes.STUDENT_NOT_IN_GROUP

    def test_get_groups_for_learner_group_set_not_found(
        self, moodle_api_client, plugin, grouping_service, course
    ):
        moodle_api_client.groups_for_user.side_effect = ExternalRequestError(
            validation_errors={"errorcode": "invalidrecord"}
        )

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == ErrorCodes.GROUP_SET_NOT_FOUND

    def test_get_groups_for_learner_raises(
        self, moodle_api_client, plugin, grouping_service, course
    ):
        moodle_api_client.groups_for_user.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )

    def test_get_groups_for_grading(self, plugin, moodle_api_client, course):
        group_set_id = 100
        api_groups = plugin.get_groups_for_grading(
            sentinel.service, course, group_set_id, sentinel.grading_student_id
        )

        moodle_api_client.groups_for_user.assert_called_once_with(
            course.lms_id,
            group_set_id,
            sentinel.grading_student_id,
        )
        assert api_groups == moodle_api_client.groups_for_user.return_value

    def test_get_groups_for_instructor(
        self, moodle_api_client, plugin, grouping_service, course
    ):
        api_groups = plugin.get_groups_for_instructor(
            grouping_service, course, sentinel.group_set_id
        )

        moodle_api_client.group_set_groups.assert_called_once_with(
            course.lms_id, sentinel.group_set_id
        )
        assert api_groups == moodle_api_client.group_set_groups.return_value

    def test_get_groups_for_instructor_raises(
        self, moodle_api_client, plugin, grouping_service, course
    ):
        moodle_api_client.group_set_groups.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )

    def test_get_groups_for_instructor_group_set_not_found(
        self, moodle_api_client, plugin, grouping_service, course
    ):
        moodle_api_client.group_set_groups.side_effect = ExternalRequestError(
            validation_errors={"errorcode": "invalidrecord"}
        )

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == ErrorCodes.GROUP_SET_NOT_FOUND

    def test_get_groups_for_instructor_group_set_empty(
        self, moodle_api_client, plugin, grouping_service, course
    ):
        moodle_api_client.group_set_groups.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == ErrorCodes.GROUP_SET_EMPTY

    def test_factory(self, pyramid_request, moodle_api_client):
        plugin = MoodleGroupingPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, MoodleGroupingPlugin)
        assert plugin._api == moodle_api_client  # noqa: SLF001

    @pytest.fixture
    def plugin(self, moodle_api_client, lti_user):
        return MoodleGroupingPlugin(moodle_api_client, lti_user)

    @pytest.fixture
    def course(self):
        course = factories.Course(lms_id=random.randint(1, 1000))
        with patch.object(course, "set_group_sets"):
            yield course
