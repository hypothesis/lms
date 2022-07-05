from unittest.mock import create_autospec, sentinel

import pytest

from lms.models import ApplicationSettings, Grouping
from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin, ErrorCodes
from lms.product.plugin.grouping_service import GroupError
from lms.resources import LTILaunchResource
from lms.services import CanvasAPIError
from tests import factories


class TestCanvasGroupingPlugin:
    @pytest.mark.parametrize("developer_key", (True, False))
    @pytest.mark.parametrize("sections_enabled", (True, False))
    def test_get_grouping_type(
        self, plugin, context, grouping_service, developer_key, sections_enabled
    ):
        context.application_instance.developer_key = developer_key
        context.course.settings.set("canvas", "sections_enabled", sections_enabled)

        assert (
            plugin.get_grouping_type(grouping_service) == Grouping.Type.SECTION
        ) == bool(developer_key and sections_enabled)

    @pytest.mark.parametrize(
        "params,is_sections",
        (
            ({}, True),
            ({"focused_user": "any", "learner_canvas_user_id": "any"}, True),
            ({"focused_user": "any"}, False),
        ),
    )
    def test_get_grouping_type_speedgrader_quirks(
        self, plugin, context, pyramid_request, grouping_service, params, is_sections
    ):
        pyramid_request.params = params
        context.application_instance.developer_key = True
        context.course.settings.set("canvas", "sections_enabled", True)

        assert (
            plugin.get_grouping_type(grouping_service) == Grouping.Type.SECTION
        ) == is_sections

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
            sentinel.group_set_id
        )
        assert canvas_api_client.group_category_groups.return_value == api_groups

    def test_get_groups_for_instructor_group_set_not_found(
        self, grouping_service, canvas_api_client, course, plugin
    ):
        canvas_api_client.group_category_groups.side_effect = CanvasAPIError()

        with pytest.raises(GroupError) as err:
            plugin.get_groups_for_instructor(
                grouping_service, course, sentinel.group_set_id
            )

        assert err.value.error_code == ErrorCodes.GROUP_SET_NOT_FOUND

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

    def test_factory(self, pyramid_request, canvas_api_client):
        plugin = CanvasGroupingPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, CanvasGroupingPlugin)
        # pylint: disable=protected-access
        assert plugin._canvas_api == canvas_api_client

    @pytest.fixture
    def course(self):
        return factories.Course(
            extra={"canvas": {"custom_canvas_course_id": sentinel.canvas_course_id}}
        )

    @pytest.fixture
    def plugin(self, context, pyramid_request, canvas_api_client):
        return CanvasGroupingPlugin(context, pyramid_request, canvas_api_client)

    @pytest.fixture
    def context(self):
        context = create_autospec(LTILaunchResource, instance=True, spec_set=True)
        context.course = factories.Course(settings=ApplicationSettings())
        return context
