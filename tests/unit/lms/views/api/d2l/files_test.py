from unittest.mock import sentinel

import pytest

from lms.views.api.d2l.files import list_files, via_url


def test_course_group_sets(pyramid_request, d2l_api_client):
    pyramid_request.matchdict = {"course_id": "test_course_id"}

    result = list_files(sentinel.context, pyramid_request)

    d2l_api_client.list_files.assert_called_once_with("test_course_id")
    assert result == d2l_api_client.list_files.return_value


def test_via_url(helpers, pyramid_request, d2l_api_client, oauth2_token_service):
    pyramid_request.matchdict = {"course_id": "COURSE_ID"}
    pyramid_request.params[
        "document_url"
    ] = "d2l://file/course/COURSE_ID/file_id/FILE_ID/"

    response = via_url(sentinel.context, pyramid_request)

    d2l_api_client.public_url.assert_called_once_with("COURSE_ID", "FILE_ID")
    helpers.via_url.assert_called_once_with(
        pyramid_request,
        d2l_api_client.public_url.return_value,
        content_type="pdf",
        headers={"Authorization": f"Bearer {oauth2_token_service.get().access_token}"},
    )
    assert response == {"via_url": helpers.via_url.return_value}


@pytest.fixture
def helpers(patch):
    return patch("lms.views.api.d2l.files.helpers")
