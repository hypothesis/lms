from unittest.mock import sentinel

import pytest

from lms.services.exceptions import FileNotFoundInCourse
from lms.views.api.d2l.files import via_url


@pytest.mark.parametrize("is_instructor", [True, False])
def test_via_url(
    d2l_api_client,
    helpers,
    pyramid_request,
    course_service,
    course_copy_plugin,
    is_instructor,
    oauth2_token_service,
    request,
):
    if is_instructor:
        request.getfixturevalue("user_is_instructor")
    course_copy_plugin.is_file_in_course.return_value = True

    response = via_url(sentinel.context, pyramid_request)

    course_service.get_by_context_id.assert_called_once_with(
        "COURSE_ID", raise_on_missing=True
    )
    course = course_service.get_by_context_id.return_value
    course.get_mapped_file_id.assert_called_once_with("FILE_ID")
    file_id = course.get_mapped_file_id.return_value

    if is_instructor:
        course_copy_plugin.is_file_in_course.assert_called_once_with(
            "COURSE_ID", file_id
        )

    d2l_api_client.public_url.assert_called_once_with(
        "COURSE_ID", course.get_mapped_file_id.return_value
    )
    helpers.via_url.assert_called_once_with(
        pyramid_request,
        d2l_api_client.public_url.return_value,
        content_type="pdf",
        headers={"Authorization": f"Bearer {oauth2_token_service.get().access_token}"},
    )
    assert response == {"via_url": helpers.via_url.return_value}


@pytest.mark.usefixtures("user_is_instructor")
def test_it_when_file_not_in_course_fixed_by_course_copy(
    d2l_api_client,
    helpers,
    pyramid_request,
    course_service,
    course_copy_plugin,
    oauth2_token_service,
):
    course_copy_plugin.is_file_in_course.return_value = False

    response = via_url(sentinel.context, pyramid_request)

    course_service.get_by_context_id.assert_called_once_with(
        "COURSE_ID", raise_on_missing=True
    )
    course = course_service.get_by_context_id.return_value
    course.get_mapped_file_id.assert_called_once_with("FILE_ID")
    file_id = course.get_mapped_file_id.return_value

    course_copy_plugin.is_file_in_course.assert_called_once_with("COURSE_ID", file_id)
    course_copy_plugin.find_matching_file_in_course.assert_called_once_with(
        file_id, "COURSE_ID"
    )
    found_file = course_copy_plugin.find_matching_file_in_course.return_value
    d2l_api_client.public_url.assert_called_once_with("COURSE_ID", found_file.lms_id)
    course.set_mapped_file_id.assert_called_once_with(file_id, found_file.lms_id)

    helpers.via_url.assert_called_once_with(
        pyramid_request,
        d2l_api_client.public_url.return_value,
        content_type="pdf",
        headers={"Authorization": f"Bearer {oauth2_token_service.get().access_token}"},
    )
    assert response == {"via_url": helpers.via_url.return_value}


@pytest.mark.usefixtures("user_is_instructor")
def test_it_when_file_not_in_course(
    d2l_api_client, course_service, course_copy_plugin, pyramid_request
):
    course_copy_plugin.is_file_in_course.return_value = False
    d2l_api_client.public_url.side_effect = FileNotFoundInCourse(
        "d2l_file_not_found_in_course_instructor", document_id="FILE_ID"
    )
    course_copy_plugin.find_matching_file_in_course.return_value = None

    with pytest.raises(FileNotFoundInCourse):
        via_url(sentinel.context, pyramid_request)

    course_service.get_by_context_id.assert_called_once_with(
        "COURSE_ID", raise_on_missing=True
    )
    course = course_service.get_by_context_id.return_value
    course.get_mapped_file_id.assert_called_once_with("FILE_ID")
    file_id = course.get_mapped_file_id.return_value

    course_copy_plugin.is_file_in_course.assert_called_once_with("COURSE_ID", file_id)
    course_copy_plugin.find_matching_file_in_course.assert_called_once_with(
        file_id, "COURSE_ID"
    )


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.matchdict = {"course_id": "COURSE_ID"}
    pyramid_request.params["document_url"] = (
        "d2l://file/course/COURSE_ID/file_id/FILE_ID/"
    )
    return pyramid_request


@pytest.fixture
def helpers(patch):
    return patch("lms.views.api.d2l.files.helpers")
