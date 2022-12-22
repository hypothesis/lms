from unittest.mock import sentinel

from lms.views.api.d2l.files import list_files


def test_course_group_sets(pyramid_request, d2l_api_client):
    pyramid_request.matchdict = {"course_id": "test_course_id"}

    result = list_files(sentinel.context, pyramid_request)

    d2l_api_client.list_files.assert_called_once_with("test_course_id")
    assert result == d2l_api_client.list_files.return_value
