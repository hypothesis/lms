from functools import partial
from unittest.mock import call, sentinel

import pytest

from lms.services import (
    CanvasAPIPermissionError,
    CanvasFileNotFoundInCourse,
    CanvasService,
)
from lms.services.canvas import factory
from tests import factories


class TestPublicURLForFile:
    # A special file id which causes CanvasAPIPermissionError errors
    MISSING_FILE_ID = "missing_file"

    def test_it_calls_the_canvas_api(self, canvas_service, public_url_for_file):
        url = public_url_for_file(file_id="file_id")

        canvas_service.api.public_url.assert_called_once_with("file_id")
        assert url == canvas_service.api.public_url.return_value

    def test_it_calls_the_canvas_api_with_a_mapped_file(
        self, canvas_service, public_url_for_file, assignment
    ):
        assignment.set_canvas_mapped_file_id("old_id", "new_id")

        public_url_for_file(file_id="old_id", module_item_configuration=assignment)

        canvas_service.api.public_url.assert_called_once_with("new_id")

    def test_it_without_check_in_course(self, canvas_service, public_url_for_file):
        public_url_for_file(check_in_course=False)

        canvas_service.api.list_files.assert_not_called()

    def test_it_with_check_in_course(self, canvas_service, public_url_for_file):
        canvas_service.api.list_files.return_value = [{"id": "file_id"}]

        public_url_for_file(
            file_id="file_id", course_id=sentinel.course_id, check_in_course=True
        )

        canvas_service.api.list_files.assert_called_once_with(sentinel.course_id)

    def test_it_raises_with_check_in_course_if_file_not_in_course(
        self, canvas_service, public_url_for_file
    ):
        canvas_service.api.list_files.return_value = []

        with pytest.raises(CanvasFileNotFoundInCourse):
            public_url_for_file(check_in_course=True)

    def test_it_remaps_a_file_when_we_get_permission_errors(
        self, canvas_service, public_url_for_file, assignment, matching_file_in_course
    ):
        public_url_for_file(
            file_id=self.MISSING_FILE_ID, module_item_configuration=assignment
        )

        canvas_service.api.public_url.assert_has_calls(
            [call(self.MISSING_FILE_ID), call(matching_file_in_course["id"])]
        )
        assert (
            assignment.get_canvas_mapped_file_id(self.MISSING_FILE_ID)
            == matching_file_in_course["id"]
        )

    def test_it_remaps_a_file_when_we_see_the_file_isnt_in_the_course(
        self, canvas_service, public_url_for_file, assignment, matching_file_in_course
    ):
        public_url_for_file(
            file_id=self.MISSING_FILE_ID,
            module_item_configuration=assignment,
            check_in_course=True,
        )

        # Note here we never call with the missing id, as we notice it before
        # with the check to see the file is in the course
        canvas_service.api.public_url.assert_called_once_with(
            matching_file_in_course["id"]
        )
        assert (
            assignment.get_canvas_mapped_file_id(self.MISSING_FILE_ID)
            == matching_file_in_course["id"]
        )

    @pytest.mark.parametrize(
        "check_in_course,exception",
        ((True, CanvasFileNotFoundInCourse), (False, CanvasAPIPermissionError)),
    )
    def test_remapping_raises_if_theres_no_file_record(
        self, public_url_for_file, file_service, check_in_course, exception
    ):
        file_service.get.return_value = None

        with pytest.raises(exception):
            public_url_for_file(
                file_id=self.MISSING_FILE_ID, check_in_course=check_in_course
            )

    @pytest.mark.usefixtures("file_record")
    @pytest.mark.parametrize(
        "check_in_course,exception",
        ((True, CanvasFileNotFoundInCourse), (False, CanvasAPIPermissionError)),
    )
    def test_remapping_raises_if_theres_no_match_in_the_course(
        self, canvas_service, public_url_for_file, check_in_course, exception
    ):
        canvas_service.api.list_files.return_value = []

        with pytest.raises(exception):
            public_url_for_file(
                file_id=self.MISSING_FILE_ID, check_in_course=check_in_course
            )

    @pytest.fixture(autouse=True)
    def canvas_api_client(self, canvas_api_client):
        def public_url(file_id):
            # Rig public_url to blow if we get MISSING_FILE_ID
            if file_id == self.MISSING_FILE_ID:
                raise CanvasAPIPermissionError()

            # Allow anything else
            return canvas_api_client.public_url.return_value

        canvas_api_client.public_url.side_effect = public_url

        return canvas_api_client

    @pytest.fixture
    def assignment(self, db_session):
        assignment = factories.ModuleItemConfiguration()
        db_session.flush()
        return assignment

    @pytest.fixture
    def public_url_for_file(self, canvas_service, assignment):
        return partial(
            canvas_service.public_url_for_file,
            module_item_configuration=assignment,
            file_id="file_id",
            course_id=sentinel.course_id,
        )


class TestAssertFileInCourse:
    def test_it_does_not_raise_if_the_file_is_in_the_course(self, canvas_service):
        return canvas_service.api.list_files.return_value == [
            {"id": "noise"},
            {"id": 2},
        ]

        canvas_service.assert_file_in_course("2", sentinel.course_id)

    def test_it_raises_if_the_file_isnt_in_the_course(self, canvas_service):
        canvas_service.api.list_files.return_value = []

        with pytest.raises(CanvasFileNotFoundInCourse):
            canvas_service.assert_file_in_course("4", sentinel.course_id)


class TestFindMatchingFileInCourse:
    def test_it_returns_the_id_if_theres_a_matching_file_in_the_course(
        self, canvas_service, file_record, matching_file_in_course
    ):
        matching_file_id = canvas_service.find_matching_file_in_course(
            sentinel.course_id, file_record
        )

        canvas_service.api.list_files.assert_called_once_with(sentinel.course_id)
        assert matching_file_id == matching_file_in_course["id"]

    def test_it_returns_None_if_theres_no_matching_file_in_the_course(
        self, canvas_service
    ):
        assert not canvas_service.find_matching_file_in_course(
            sentinel.course_id, factories.File()
        )


class TestFactory:
    def test_it(self, pyramid_request, CanvasService, canvas_api_client, file_service):
        result = factory("*any*", request=pyramid_request)

        assert result == CanvasService.return_value
        CanvasService.assert_called_once_with(
            canvas_api=canvas_api_client, file_service=file_service
        )

    @pytest.fixture
    def CanvasService(self, patch):
        return patch("lms.services.canvas.CanvasService")


@pytest.fixture
def canvas_service(canvas_api_client, file_service):
    return CanvasService(canvas_api_client, file_service)


@pytest.fixture
def file_record(file_service):
    file_record = factories.File()
    file_service.get.return_value = file_record

    return file_record


@pytest.fixture
def matching_file_in_course(file_record, canvas_service):
    # Create a match which is tailored to the file record
    matching_file_in_course = {
        "id": "new_file",
        "display_name": file_record.name,
        "size": file_record.size,
    }

    # Ensure `list_files` returns it
    canvas_service.api.list_files.return_value = [matching_file_in_course]

    return matching_file_in_course
