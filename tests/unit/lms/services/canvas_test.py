from functools import partial
from unittest.mock import call, sentinel

import pytest

from lms.services import CanvasAPIPermissionError, CanvasService
from lms.services.canvas import factory
from lms.services.exceptions import FileNotFoundInCourse
from tests import factories


class TestPublicURLForFile:
    @pytest.mark.parametrize("check_in_course", [True, False])
    def test_the_happy_path(
        self,
        canvas_api_client,
        course_copy_plugin,
        check_in_course,
        public_url_for_file,
    ):
        url = public_url_for_file(sentinel.file_id, check_in_course=check_in_course)

        if check_in_course:
            course_copy_plugin.is_file_in_course.assert_called_once_with(
                sentinel.course_id, sentinel.file_id
            )
        else:
            course_copy_plugin.is_file_in_course.assert_not_called()
        canvas_api_client.public_url.assert_called_once_with(sentinel.file_id)
        assert url == canvas_api_client.public_url.return_value

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_theres_a_mapped_file_id_it_uses_it(
        self, canvas_api_client, course_copy_plugin, public_url_for_file
    ):
        url = public_url_for_file(sentinel.file_id, check_in_course=True)

        course_copy_plugin.is_file_in_course.assert_called_once_with(
            sentinel.course_id, sentinel.mapped_file_id
        )
        canvas_api_client.public_url.assert_called_once_with(sentinel.mapped_file_id)
        assert url == canvas_api_client.public_url.return_value

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_the_file_isnt_in_the_course_it_finds_a_matching_file_instead(
        self,
        canvas_api_client,
        course_copy_plugin,
        assignment,
        public_url_for_file,
    ):
        course_copy_plugin.is_file_in_course.return_value = False
        course_copy_plugin.find_matching_file_in_course.return_value = (
            sentinel.found_file_id
        )

        url = public_url_for_file(sentinel.file_id, check_in_course=True)

        course_copy_plugin.find_matching_file_in_course.assert_called_once_with(
            sentinel.course_id, {sentinel.file_id, sentinel.mapped_file_id}
        )
        assert (
            assignment.get_canvas_mapped_file_id(sentinel.file_id)
            == sentinel.found_file_id
        )
        canvas_api_client.public_url.assert_called_once_with(sentinel.found_file_id)
        assert url == canvas_api_client.public_url.return_value

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_the_file_isnt_in_the_course_and_theres_no_matching_file_it_raises(
        self, course_copy_plugin, public_url_for_file
    ):
        course_copy_plugin.is_file_in_course.return_value = False
        course_copy_plugin.find_matching_file_in_course.return_value = None

        with pytest.raises(FileNotFoundInCourse):
            public_url_for_file(sentinel.file_id, check_in_course=True)

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_theres_a_permissions_error_it_finds_a_matching_file_instead(
        self,
        canvas_api_client,
        course_copy_plugin,
        assignment,
        public_url_for_file,
    ):
        canvas_api_client.public_url.side_effect = [
            CanvasAPIPermissionError,
            sentinel.url,
        ]
        course_copy_plugin.find_matching_file_in_course.return_value = (
            sentinel.found_file_id
        )

        url = public_url_for_file(sentinel.file_id)

        course_copy_plugin.find_matching_file_in_course.assert_called_once_with(
            sentinel.course_id, {sentinel.file_id, sentinel.mapped_file_id}
        )
        assert (
            assignment.get_canvas_mapped_file_id(sentinel.file_id)
            == sentinel.found_file_id
        )
        assert canvas_api_client.public_url.call_args_list == [
            call(sentinel.mapped_file_id),
            call(sentinel.found_file_id),
        ]
        assert url == sentinel.url

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_theres_a_permissions_error_and_theres_no_matching_file_it_raises(
        self, canvas_api_client, course_copy_plugin, public_url_for_file
    ):
        canvas_api_client.public_url.side_effect = CanvasAPIPermissionError
        course_copy_plugin.find_matching_file_in_course.return_value = None

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file(sentinel.file_id)

    def test_it_doesnt_save_a_mapped_file_id_if_getting_that_files_public_url_fails(
        self,
        canvas_api_client,
        course_copy_plugin,
        assignment,
        public_url_for_file,
    ):
        canvas_api_client.public_url.side_effect = CanvasAPIPermissionError
        course_copy_plugin.find_matching_file_in_course.return_value = (
            sentinel.found_file_id
        )

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file(sentinel.file_id)

        assert (
            assignment.get_canvas_mapped_file_id(sentinel.file_id) == sentinel.file_id
        )

    @pytest.fixture
    def assignment(self, db_session):
        assignment = factories.Assignment()
        db_session.flush()
        return assignment

    @pytest.fixture
    def with_mapped_file_id(self, assignment):
        assignment.set_canvas_mapped_file_id(sentinel.file_id, sentinel.mapped_file_id)

    @pytest.fixture
    def public_url_for_file(self, canvas_service, assignment):
        return partial(
            canvas_service.public_url_for_file,
            assignment,
            current_course_id=sentinel.course_id,
        )


class TestFactory:
    def test_it(
        self, pyramid_request, CanvasService, canvas_api_client, course_copy_plugin
    ):
        result = factory(sentinel.context, request=pyramid_request)

        assert result == CanvasService.return_value
        CanvasService.assert_called_once_with(
            canvas_api=canvas_api_client, course_copy_plugin=course_copy_plugin
        )

    @pytest.fixture
    def CanvasService(self, patch):
        return patch("lms.services.canvas.CanvasService")


@pytest.fixture
def canvas_service(canvas_api_client, course_copy_plugin):
    return CanvasService(canvas_api_client, course_copy_plugin)
