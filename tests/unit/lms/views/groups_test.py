from unittest.mock import sentinel

from lms.views.api.groups import course_group_sets


def test_course_group_sets(pyramid_request, grouping_plugin, course_service):
    pyramid_request.matchdict = {"course_id": sentinel.course_id}

    result = course_group_sets(sentinel.context, pyramid_request)

    course_service.get_by_context_id.assert_called_once_with(sentinel.course_id)
    grouping_plugin.get_group_sets.assert_called_once_with(
        course_service.get_by_context_id.return_value
    )
    assert result == grouping_plugin.get_group_sets.return_value
