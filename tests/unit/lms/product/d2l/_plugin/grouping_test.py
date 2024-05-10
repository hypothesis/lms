from unittest.mock import Mock, patch, sentinel

import pytest

from lms.models import Grouping
from lms.product.d2l._plugin.grouping import D2LGroupingPlugin, ErrorCodes
from lms.product.plugin.grouping import GroupError
from lms.services.exceptions import ExternalRequestError
from tests import factories


class TestD2LGroupingPlugin:
    def test_get_group_sets(self, plugin, d2l_api_client, course):
        api_group_sets = plugin.get_group_sets(course)

        d2l_api_client.course_group_sets.assert_called_once_with(course.lms_id)
        course.set_group_sets.assert_called_once_with(
            d2l_api_client.course_group_sets.return_value
        )
        assert api_group_sets == d2l_api_client.course_group_sets.return_value

    def test_get_groups_for_learner(
        self, d2l_api_client, plugin, grouping_service, course
    ):
        api_groups = plugin.get_groups_for_learner(
            grouping_service, course, sentinel.group_set_id
        )

        d2l_api_client.group_set_groups.assert_called_once_with(
            course.lms_id, sentinel.group_set_id, sentinel.api_user_id
        )
        assert api_groups == d2l_api_client.group_set_groups.return_value

    def test_get_groups_for_learner_when_no_groups(
        self, d2l_api_client, plugin, grouping_service, course
    ):
        d2l_api_client.group_set_groups.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == ErrorCodes.STUDENT_NOT_IN_GROUP

    def test_get_groups_for_learner_group_set_not_found(
        self, d2l_api_client, plugin, grouping_service, course
    ):
        d2l_api_client.group_set_groups.side_effect = ExternalRequestError(
            response=Mock(status_code=404)
        )

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == ErrorCodes.GROUP_SET_NOT_FOUND

    def test_get_groups_for_learner_raises(
        self, d2l_api_client, plugin, grouping_service, course
    ):
        d2l_api_client.group_set_groups.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )

    def test_get_groups_for_grading(self, plugin, grouping_service, course):
        group_set_id = 100
        api_groups = plugin.get_groups_for_grading(
            grouping_service, course, group_set_id, sentinel.grading_student_id
        )

        grouping_service.get_course_groupings_for_user.assert_called_once_with(
            course,
            sentinel.grading_student_id,
            type_=Grouping.Type.D2L_GROUP,
            group_set_id=group_set_id,
        )
        assert api_groups == grouping_service.get_course_groupings_for_user.return_value

    def test_get_groups_for_instructor(
        self, d2l_api_client, plugin, grouping_service, course
    ):
        api_groups = plugin.get_groups_for_instructor(
            grouping_service, course, sentinel.group_set_id
        )

        d2l_api_client.group_set_groups.assert_called_once_with(
            course.lms_id, sentinel.group_set_id
        )
        assert api_groups == d2l_api_client.group_set_groups.return_value

    def test_get_groups_for_instructor_raises(
        self, d2l_api_client, plugin, grouping_service, course
    ):
        d2l_api_client.group_set_groups.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )

    def test_get_groups_for_instructor_group_set_not_found(
        self, d2l_api_client, plugin, grouping_service, course
    ):
        d2l_api_client.group_set_groups.side_effect = ExternalRequestError(
            response=Mock(status_code=404)
        )

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == ErrorCodes.GROUP_SET_NOT_FOUND

    def test_get_groups_for_instructor_group_set_empty(
        self, d2l_api_client, plugin, grouping_service, course
    ):
        d2l_api_client.group_set_groups.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )
        assert err.value.error_code == ErrorCodes.GROUP_SET_EMPTY

    def test_factory(self, pyramid_request, d2l_api_client, misc_plugin):
        plugin = D2LGroupingPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, D2LGroupingPlugin)
        assert plugin._d2l_api == d2l_api_client  # noqa: SLF001
        assert plugin._misc_plugin == misc_plugin  # noqa: SLF001

    @pytest.fixture
    def plugin(self, d2l_api_client, misc_plugin):
        return D2LGroupingPlugin(d2l_api_client, sentinel.api_user_id, misc_plugin)

    @pytest.fixture
    def course(self):
        course = factories.Course()
        with patch.object(course, "set_group_sets"):
            yield course
