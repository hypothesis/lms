from unittest.mock import sentinel

from lms.views.api.moodle.files import list_files


def test_course_group_sets(pyramid_request, moodle_api_client):
    pyramid_request.matchdict = {"course_id": "test_course_id"}

    result = list_files(sentinel.context, pyramid_request)

    moodle_api_client.list_files.assert_called_once_with("test_course_id")
    assert result == moodle_api_client.list_files.return_value
