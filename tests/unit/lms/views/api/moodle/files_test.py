from unittest.mock import sentinel

import pytest

from lms.views.api.moodle.files import list_files, via_url


def test_course_group_sets(pyramid_request, moodle_api_client):
    pyramid_request.matchdict = {"course_id": "test_course_id"}

    result = list_files(sentinel.context, pyramid_request)

    moodle_api_client.list_files.assert_called_once_with("test_course_id")
    assert result == moodle_api_client.list_files.return_value


def test_via_url(
    moodle_api_client,
    helpers,
    pyramid_request,
):
    type(moodle_api_client).token = "TOKEN"
    pyramid_request.params["document_url"] = "moodle://file/url/URL"

    response = via_url(sentinel.context, pyramid_request)

    helpers.via_url.assert_called_once_with(
        pyramid_request,
        "URL",
        content_type="pdf",
        query={"token": moodle_api_client.token},
    )
    assert response == {"via_url": helpers.via_url.return_value}


@pytest.fixture(autouse=True)
def helpers(patch):
    return patch("lms.views.api.moodle.files.helpers")
