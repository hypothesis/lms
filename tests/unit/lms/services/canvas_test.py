from functools import partial
from unittest.mock import DEFAULT, call, sentinel

import pytest

from lms.services import (
    CanvasAPIPermissionError,
    CanvasFileNotFoundInCourse,
    CanvasService,
)
from lms.services.canvas import factory
from tests import factories


class TestPublicURLForFile:
    def test_without_check_in_course_and_without_a_mapped_file_id(
        self, canvas_service, file_from_current_course, public_url_for_file
    ):
        # This is what happens during a normal student assignment launch:
        # check_in_course is False and there's no mapped_file_id in the DB.

        url = public_url_for_file(file_id=str(file_from_current_course["id"]))

        # check_in_course was False, so it didn't call list_files() to check
        # whether the file_id was in the course.
        canvas_service.api.list_files.assert_not_called()

        # It calls the Canvas API with the file_id and returns the public URL.
        canvas_service.api.public_url.assert_called_once_with(
            str(file_from_current_course["id"])
        )
        assert url == canvas_service.api.public_url.return_value

    def test_if_check_in_course_is_True_it_checks_that_the_file_is_in_the_course(
        self, canvas_service, file_from_current_course, public_url_for_file
    ):
        # This is what happens during a normal instructor launch;
        # check_in_course is True and there's no mapped_file_id in the DB.

        url = public_url_for_file(
            file_id=str(file_from_current_course["id"]), check_in_course=True
        )

        # check_in_course was True so it called list_files() to check whether
        # file_id was in the course.
        canvas_service.api.list_files.assert_called_once_with(sentinel.course_id)

        # It calls the Canvas API with the file_id and returns the public URL.
        canvas_service.api.public_url.assert_called_once_with(
            str(file_from_current_course["id"])
        )
        assert url == canvas_service.api.public_url.return_value

    def test_if_theres_a_mapped_file_id_it_uses_it(
        self,
        canvas_service,
        module_item_configuration,
        file_from_current_course,
        file_from_a_different_course,
        public_url_for_file,
    ):
        # If there's a mapped_file_id in the DB it gets used instead of the
        # given file_id.
        #
        # This is what happens when a user launches a course-copied assignment
        # that has previously been fixed (we've previously stored a
        # mapped_file_id in the DB).

        # Store a mapped_file_id in the DB. This would have been done by a
        # previous request.
        module_item_configuration.set_canvas_mapped_file_id(
            str(file_from_a_different_course["id"]), str(file_from_current_course["id"])
        )

        url = public_url_for_file(
            file_id=str(file_from_a_different_course["id"]), check_in_course=True
        )

        # It checks that the mapped_file_id is in the course (not the original file_id).
        canvas_service.api.list_files.assert_called_once_with(sentinel.course_id)

        # It called public_url() with the mapped_file_id rather than with the
        # original file_id, and returned the public URL.
        canvas_service.api.public_url.assert_called_once_with(
            str(file_from_current_course["id"])
        )
        assert url == canvas_service.api.public_url.return_value

    def test_file_not_found_in_course_and_matching_file_found(
        self,
        canvas_service,
        file_service,
        module_item_configuration,
        file_from_current_course,
        file_from_a_different_course,
        public_url_for_file,
    ):
        # This is what happens when an instructor launches an assignment whose
        # file_id is *not* in the current course.
        file_service.get.return_value = factories.File(
            name=file_from_current_course["display_name"],
            size=file_from_current_course["size"],
        )

        url = public_url_for_file(
            file_id=str(file_from_a_different_course["id"]), check_in_course=True
        )

        # It looked up the given file_id in the DB.
        file_service.get.assert_called_once_with(
            str(file_from_a_different_course["id"]), type_="canvas_file"
        )
        # It stored a mapping from the given file_id to found_file_id.
        assert module_item_configuration.get_canvas_mapped_file_id(
            str(file_from_a_different_course["id"])
        ) == str(file_from_current_course["id"])
        # It got the found_file_id's public URL and returned it.
        canvas_service.api.public_url.assert_called_once_with(
            str(file_from_current_course["id"])
        )
        assert url == canvas_service.api.public_url.return_value

    def test_permissions_error_and_matching_file_found(
        self,
        canvas_service,
        file_service,
        module_item_configuration,
        file_from_current_course,
        file_from_a_different_course,
        public_url_for_file,
    ):
        # This is what happens when a student launches an assignment whose
        # file_id is *not* in the current course.
        canvas_service.api.public_url.side_effect = [CanvasAPIPermissionError, DEFAULT]
        file_service.get.return_value = factories.File(
            name=file_from_current_course["display_name"],
            size=file_from_current_course["size"],
        )

        url = public_url_for_file(file_id=str(file_from_a_different_course["id"]))

        # It looked up the given file_id in the DB.
        file_service.get.assert_called_once_with(
            str(file_from_a_different_course["id"]), type_="canvas_file"
        )
        # It stored a mapping from the given file_id to found_file_id.
        assert module_item_configuration.get_canvas_mapped_file_id(
            str(file_from_a_different_course["id"])
        ) == str(file_from_current_course["id"])
        # It got found_file_id's public URL and returned it.
        assert canvas_service.api.public_url.call_args_list == [
            call(str(file_from_a_different_course["id"])),
            call(str(file_from_current_course["id"])),
        ]
        assert url == canvas_service.api.public_url.return_value

    def test_file_not_found_in_course_but_no_file_info(
        self, file_service, file_from_a_different_course, public_url_for_file
    ):
        # This is what happens when a teacher launches an assignment whose
        # file_id is *not* in the current course and we don't have a record of
        # the file_id in our DB. Without a record we can't search for a
        # matching file so we raise an error.

        # There's no record of the file_id in the DB.
        file_service.get.return_value = None

        with pytest.raises(CanvasFileNotFoundInCourse):
            public_url_for_file(
                str(file_from_a_different_course["id"]), check_in_course=True
            )

    def test_file_not_found_in_course_but_no_matching_file(
        self, file_service, file_from_a_different_course, public_url_for_file
    ):
        # This is what happens when a teacher launches an assignment whose
        # file_id is *not* in the current course and even though we do have a
        # record of this file_id in our DB we don't find a matching file in the
        # current course. Since we can't find a matching file we can't fix the
        # assignment so we raise an error.

        # The file record that we find in our DB. Its name doesn't match any
        # file in the current course.
        file_service.get.return_value = factories.File(name="foo")

        with pytest.raises(CanvasFileNotFoundInCourse):
            public_url_for_file(
                file_id=str(file_from_a_different_course["id"]), check_in_course=True
            )

    def test_permissions_error_but_no_file_info(
        self,
        canvas_service,
        file_service,
        file_from_a_different_course,
        public_url_for_file,
    ):
        # This is what happens when a student launches an assignment whose
        # file_id is *not* in the current course and we don't have a record of
        # the file_id in our DB. Without a record we can't search for a
        # matching file so we raise an error.
        canvas_service.api.public_url.side_effect = CanvasAPIPermissionError
        file_service.get.return_value = None

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file(file_id=str(file_from_a_different_course["id"]))

    def test_permissions_error_but_no_matching_file(
        self,
        canvas_service,
        file_service,
        file_from_a_different_course,
        public_url_for_file,
    ):
        # This is what happens when a student launches an assignment whose
        # file_id is *not* in the current course and even though we do have a
        # record of this file_id in our DB we don't find a matching file in the
        # current course. Since we can't find a matching file we can't fix the
        # assignment so we raise an error.
        canvas_service.api.public_url.side_effect = CanvasAPIPermissionError

        # The file record that we find in our DB. Its name doesn't match any
        # file in the current course.
        file_service.get.return_value = factories.File(name="foo")

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file(file_id=str(file_from_a_different_course["id"]))

    @pytest.fixture
    def module_item_configuration(self, db_session):
        module_item_configuration = factories.ModuleItemConfiguration()
        db_session.flush()
        return module_item_configuration

    @pytest.fixture
    def public_url_for_file(self, canvas_service, module_item_configuration):
        return partial(
            canvas_service.public_url_for_file,
            module_item_configuration,
            course_id=sentinel.course_id,
        )

    @pytest.fixture
    def file_from_current_course(self, canvas_service):
        """Return the Canvas API file dict for a file that *is* in the current course."""
        return canvas_service.api.list_files.return_value[1]

    @pytest.fixture
    def file_from_a_different_course(self):
        """Return the Canvas API file dict for a file from a *different* course."""
        return {"id": 4, "display_name": "File 4", "size": 4096}


class TestAssertFileInCourse:
    def test_it_does_not_raise_if_the_file_is_in_the_course(self, canvas_service):
        canvas_service.assert_file_in_course("2", sentinel.course_id)

    def test_it_raises_if_the_file_isnt_in_the_course(self, canvas_service):
        with pytest.raises(CanvasFileNotFoundInCourse):
            canvas_service.assert_file_in_course("4", sentinel.course_id)


class TestFindMatchingFileInCourse:
    def test_it_returns_the_id_if_theres_a_matching_file_in_the_course(
        self, canvas_service
    ):
        # The file dict from the Canvas API that we expect the search to match.
        matching_file_dict = canvas_service.api.list_files.return_value[1]

        file_ = factories.File(
            name=matching_file_dict["display_name"],
            size=matching_file_dict["size"],
        )

        matching_file_id = canvas_service.find_matching_file_in_course(
            sentinel.course_id, file_
        )

        canvas_service.api.list_files.assert_called_once_with(sentinel.course_id)
        assert matching_file_id == str(matching_file_dict["id"])

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
    canvas_service = CanvasService(canvas_api_client, file_service)
    canvas_service.api.list_files.return_value = [
        {"id": 1, "display_name": "File 1", "size": 1024},
        {
            "id": 2,
            "display_name": "File 2",
            "size": 2048,
        },
        {
            "id": 3,
            "display_name": "File 3",
            "size": 3072,
        },
    ]
    return canvas_service
