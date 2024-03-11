from unittest.mock import Mock, sentinel

import pytest

from lms.services.exceptions import FileNotFoundInCourse
from lms.views.api.moodle.files import list_files, via_url


def test_list_files(pyramid_request, moodle_api_client):
    pyramid_request.matchdict = {"course_id": "test_course_id"}

    result = list_files(sentinel.context, pyramid_request)

    moodle_api_client.list_files.assert_called_once_with("test_course_id")
    assert result == moodle_api_client.list_files.return_value


@pytest.mark.usefixtures("course_copy_plugin")
def test_via_url(
    helpers,
    moodle_api_client,
    pyramid_request,
    lti_user,
    course_service,
):
    type(moodle_api_client).token = "TOKEN"
    lti_user.lti.course_id = course_service.get_by_context_id.return_value.lms_id = (
        "COURSE_ID"
    )
    pyramid_request.params["document_url"] = "moodle://file/course/COURSE_ID/url/URL"

    response = via_url(sentinel.context, pyramid_request)

    helpers.via_url.assert_called_once_with(
        pyramid_request,
        "URL",
        content_type="pdf",
        query={"token": moodle_api_client.token},
    )
    assert response == {"via_url": helpers.via_url.return_value}


@pytest.mark.usefixtures("course_copy_plugin")
def test_via_url_copied_with_mapped_id(
    helpers,
    pyramid_request,
    course_service,
    lti_user,
    moodle_api_client,
):
    pyramid_request.params["document_url"] = "moodle://file/course/COURSE_ID/url/URL"
    type(moodle_api_client).token = "TOKEN"
    lti_user.lti.course_id = course_service.get_by_context_id.return_value.lms_id = (
        "OTHER_COURSE_ID"
    )
    course_service.get_by_context_id.return_value.get_mapped_file_id.return_value = (
        "OTHER_FILE_URL"
    )

    response = via_url(sentinel.context, pyramid_request)

    helpers.via_url.assert_called_once_with(
        pyramid_request,
        "OTHER_FILE_URL",
        content_type="pdf",
        query={"token": moodle_api_client.token},
    )
    assert response == {"via_url": helpers.via_url.return_value}


@pytest.mark.usefixtures("moodle_api_client")
def test_via_url_copied_no_page_found(
    pyramid_request,
    course_service,
    course_copy_plugin,
    lti_user,
):
    pyramid_request.params["document_url"] = "moodle://file/course/COURSE_ID/url/URL"
    lti_user.lti.course_id = course_service.get_by_context_id.return_value.lms_id = (
        "OTHER_COURSE_ID"
    )
    course_service.get_by_context_id.return_value.get_mapped_file_id.return_value = (
        "URL"
    )
    course_copy_plugin.find_matching_file_in_course.return_value = None

    with pytest.raises(FileNotFoundInCourse):
        via_url(sentinel.context, pyramid_request)

    course_copy_plugin.find_matching_file_in_course.assert_called_once_with(
        "URL", "OTHER_COURSE_ID"
    )


def test_via_url_copied_found_page(
    pyramid_request,
    course_service,
    course_copy_plugin,
    helpers,
    lti_user,
    moodle_api_client,
):
    type(moodle_api_client).token = "TOKEN"
    lti_user.lti.course_id = course_service.get_by_context_id.return_value.lms_id = (
        "OTHER_COURSE_ID"
    )
    pyramid_request.params["document_url"] = "moodle://file/course/COURSE_ID/url/URL"
    course_service.get_by_context_id.return_value.get_mapped_file_id.return_value = (
        "URL"
    )

    course_copy_plugin.find_matching_file_in_course.return_value = Mock(
        lms_id="OTHER_FILE_URL"
    )

    response = via_url(sentinel.context, pyramid_request)

    course_copy_plugin.find_matching_file_in_course.assert_called_once_with(
        "URL", "OTHER_COURSE_ID"
    )
    course_service.get_by_context_id.return_value.set_mapped_file_id(
        "URL", "OTHER_FILE_URL"
    )

    helpers.via_url.assert_called_once_with(
        pyramid_request,
        "OTHER_FILE_URL",
        content_type="pdf",
        query={"token": moodle_api_client.token},
    )
    assert response == {"via_url": helpers.via_url.return_value}


@pytest.fixture(autouse=True)
def helpers(patch):
    return patch("lms.views.api.moodle.files.helpers")
