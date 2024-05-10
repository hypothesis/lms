from unittest.mock import sentinel

import pytest

from lms.models import JSONSettings
from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin, ErrorCodes
from lms.product.plugin.grouping import GroupError
from lms.services import CanvasAPIError
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

    def test_get_sections_for_instructor_with_strict_membership(
        self, canvas_api_client, course, grouping_service, plugin
    ):
        plugin._strict_section_membership = True  # noqa: SLF001

        api_groups = plugin.get_sections_for_instructor(grouping_service, course)

        canvas_api_client.authenticated_users_sections.assert_called_once_with(
            sentinel.canvas_course_id
        )
        assert api_groups == canvas_api_client.authenticated_users_sections.return_value

    def test_get_sections_for_grading(
        self, canvas_api_client, course, grouping_service, plugin
    ):
        canvas_api_client.course_sections.return_value = [{"id": 1}, {"id": 2}]
        canvas_api_client.users_sections.return_value = [{"id": 1}]

        api_groups = plugin.get_sections_for_grading(
            grouping_service, course, sentinel.grading_student_id
        )

        canvas_api_client.course_sections.assert_called_once_with(
            sentinel.canvas_course_id
        )
        canvas_api_client.users_sections.assert_called_once_with(
            sentinel.grading_student_id, sentinel.canvas_course_id
        )

        assert api_groups == [{"id": 1}]

    def test_get_group_sets(self, plugin, canvas_api_client, course):
        api_group_sets = plugin.get_group_sets(course)

        canvas_api_client.course_group_categories.assert_called_once_with(
            sentinel.canvas_course_id
        )
        assert api_group_sets == canvas_api_client.course_group_categories.return_value

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
        assert api_groups == canvas_api_client.current_user_groups.return_value

    def test_get_groups_for_learner_not_in_group(
        self, grouping_service, canvas_api_client, course, plugin
    ):
        canvas_api_client.current_user_groups.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_learner(
                grouping_service, course, sentinel.group_set_id
            )

        assert err.value.error_code == ErrorCodes.STUDENT_NOT_IN_GROUP

    def test_get_groups_for_instructor(
        self, canvas_api_client, grouping_service, plugin, course
    ):
        api_groups = plugin.get_groups_for_instructor(
            grouping_service, course, sentinel.group_set_id
        )

        canvas_api_client.group_category_groups.assert_called_once_with(
            sentinel.canvas_course_id, sentinel.group_set_id
        )
        assert canvas_api_client.group_category_groups.return_value == api_groups

    def test_get_groups_for_instructor_group_set_not_found(
        self, grouping_service, canvas_api_client, course, plugin, course_service
    ):
        course_service.find_group_set.return_value = None
        canvas_api_client.group_category_groups.side_effect = CanvasAPIError()

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )

        course_service.find_group_set.assert_called_once_with(
            group_set_id=sentinel.group_set_id
        )
        assert err.value.error_code == ErrorCodes.GROUP_SET_NOT_FOUND
        assert err.value.details == {
            "group_set_id": sentinel.group_set_id,
            "group_set_name": None,
        }

    def test_get_groups_for_instructor_group_set_not_found_with_original_name(
        self, grouping_service, canvas_api_client, course, plugin, course_service
    ):
        course_service.find_group_set.return_value = {"name": sentinel.name}
        canvas_api_client.group_category_groups.side_effect = CanvasAPIError()

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )

        course_service.find_group_set.assert_called_once_with(
            group_set_id=sentinel.group_set_id
        )
        assert err.value.error_code == ErrorCodes.GROUP_SET_NOT_FOUND
        assert err.value.details == {
            "group_set_name": sentinel.name,
            "group_set_id": sentinel.group_set_id,
        }

    def test_get_groups_for_instructor_group_set_empty(
        self, grouping_service, canvas_api_client, course, plugin
    ):
        canvas_api_client.group_category_groups.return_value = []

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )

        assert err.value.error_code == ErrorCodes.GROUP_SET_EMPTY

    def test_get_groups_for_grading(
        self, canvas_api_client, grouping_service, plugin, course
    ):
        api_groups = plugin.get_groups_for_grading(
            grouping_service, course, sentinel.group_set_id, sentinel.grading_student_id
        )

        canvas_api_client.user_groups.assert_called_once_with(
            sentinel.canvas_course_id,
            sentinel.grading_student_id,
            sentinel.group_set_id,
        )
        assert canvas_api_client.user_groups.return_value == api_groups

    def test_get_groups_for_grading_fallback_not_found(
        self, canvas_api_client, grouping_service, plugin, course
    ):
        canvas_api_client.user_groups.return_value = []

        all_groups = plugin.get_groups_for_grading(
            grouping_service, course, sentinel.group_set_id, sentinel.grading_student_id
        )

        canvas_api_client.user_groups.assert_called_once_with(
            sentinel.canvas_course_id,
            sentinel.grading_student_id,
            sentinel.group_set_id,
        )
        canvas_api_client.group_category_groups.assert_called_once_with(
            sentinel.canvas_course_id, sentinel.group_set_id
        )
        assert canvas_api_client.group_category_groups.return_value == all_groups

    def test_sections_enabled_speedgrader(self, plugin, pyramid_request):
        pyramid_request.params.update({"focused_user": sentinel.focused_user})

        assert not plugin.sections_enabled(
            pyramid_request, sentinel.ai, sentinel.course
        )

    def test_sections_enabled_developer_key(self, plugin, pyramid_request):
        application_instance = factories.ApplicationInstance(developer_key=None)
        assert not plugin.sections_enabled(
            pyramid_request, application_instance, sentinel.course
        )

    @pytest.mark.parametrize("enabled", [True, False])
    def test_sections_enabled_course_settings(self, plugin, enabled, pyramid_request):
        application_instance = factories.ApplicationInstance(developer_key=True)
        course = factories.Course(
            settings=JSONSettings({"canvas": {"sections_enabled": enabled}})
        )

        assert (
            plugin.sections_enabled(pyramid_request, application_instance, course)
            == enabled
        )

    def test_factory(self, pyramid_request, canvas_api_client):
        plugin = CanvasGroupingPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, CanvasGroupingPlugin)
        assert plugin._canvas_api == canvas_api_client  # noqa: SLF001

    @pytest.fixture
    def course(self):
        return factories.Course(
            extra={"canvas": {"custom_canvas_course_id": sentinel.canvas_course_id}}
        )

    @pytest.fixture
    def plugin(self, canvas_api_client, pyramid_request):
        return CanvasGroupingPlugin(
            canvas_api_client, strict_section_membership=False, request=pyramid_request
        )
