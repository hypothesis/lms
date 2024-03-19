from unittest.mock import sentinel

from lms.views.api.files import list_files


def test_list_files(pyramid_request):
    pyramid_request.matchdict = {"course_id": "test_course_id"}

    result = list_files(sentinel.context, pyramid_request)

    pyramid_request.product.api_client.list_files.assert_called_once_with(
        "test_course_id"
    )
    assert result == pyramid_request.product.api_client.list_files.return_value
