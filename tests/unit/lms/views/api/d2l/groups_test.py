from unittest.mock import sentinel

from lms.views.api.d2l.groups import course_group_sets


def test_course_group_sets(pyramid_request, d2l_api_client):
    pyramid_request.matchdict = {"course_id": "test_course_id"}

    result = course_group_sets(sentinel.context, pyramid_request)

    assert result == d2l_api_client.course_group_sets.return_value
    d2l_api_client.course_group_sets.assert_called_once_with("test_course_id")
