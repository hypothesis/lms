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
    def test_without_check_in_course(
        self,
        canvas_service,
        canvas_api_client,
        module_item_configuration,
        file_id_from_current_course,
    ):
        # This is what happens during a normal student assignment launch.
        url = canvas_service.public_url_for_file(
            module_item_configuration, file_id_from_current_course, sentinel.course_id
        )

        # check_in_course was False, so it didn't call list_files() to check
        # whether the file_id was in the course.
        canvas_api_client.list_files.assert_not_called()

        # It calls the Canvas API with the file_id and returns the public URL.
        canvas_api_client.public_url.assert_called_once_with(
            file_id_from_current_course
        )
        assert url == canvas_api_client.public_url.return_value

    def test_with_check_in_course(
        self,
        canvas_service,
        canvas_api_client,
        module_item_configuration,
        file_id_from_current_course,
    ):
        # This is what happens during a normal instructor launch.
        url = canvas_service.public_url_for_file(
            module_item_configuration,
            file_id_from_current_course,
            sentinel.course_id,
            check_in_course=True,
        )

        # check_in_course was True so it called list_files() to check whether
        # file_id was in the course.
        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)

        # It calls the Canvas API with the file_id and returns the public URL.
        canvas_api_client.public_url.assert_called_once_with(
            file_id_from_current_course
        )
        assert url == canvas_api_client.public_url.return_value

    def test_with_mapped_file_id_and_without_check_in_course(
        self,
        canvas_service,
        canvas_api_client,
        module_item_configuration,
        file_id_from_current_course,
        file_id_from_a_different_course,
    ):
        # This is what happens when a student launches a course-copied
        # assignment that has already been fixed (we've already stored a
        # mapped_file_id in the DB).

        # Store a mapped_file_id in the DB. This would have been done by a
        # previous request.
        module_item_configuration.set_mapped_file_id(
            file_id_from_a_different_course, file_id_from_current_course
        )

        url = canvas_service.public_url_for_file(
            module_item_configuration,
            file_id_from_a_different_course,
            sentinel.course_id,
        )

        # check_in_course was False, so it didn't call list_files() to check
        # whether the file_id was in the course.
        canvas_api_client.list_files.assert_not_called()

        # It called public_url() with the mapped_file_id rather than with the
        # original file_id, and returned the public URL.
        canvas_api_client.public_url.assert_called_once_with(
            file_id_from_current_course
        )
        assert url == canvas_api_client.public_url.return_value

    def test_with_mapped_file_id_and_check_in_course(
        self,
        canvas_service,
        canvas_api_client,
        module_item_configuration,
        file_id_from_current_course,
        file_id_from_a_different_course,
    ):
        # This is what happens when an instructor launches a course-copied
        # assignment that has already been fixed (we've already stored a
        # mapped_file_id in the DB).

        # Store a mapped_file_id in the DB. This would have been done by a
        # previous request.
        module_item_configuration.set_mapped_file_id(
            file_id_from_a_different_course, file_id_from_current_course
        )

        url = canvas_service.public_url_for_file(
            module_item_configuration,
            file_id_from_a_different_course,
            sentinel.course_id,
            check_in_course=True,
        )

        # check_in_course was True so it called list_files() to check whether
        # mapped_file_id was in the course.
        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)

        # It called public_url() with the mapped_file_id rather than with the
        # original file_id, and returned the public URL.
        canvas_api_client.public_url.assert_called_once_with(
            file_id_from_current_course
        )
        assert url == canvas_api_client.public_url.return_value

    def test_file_not_found_in_course_and_matching_file_found(
        self,
        canvas_service,
        canvas_api_client,
        module_item_configuration,
        file_service,
        file_from_current_course,
        file_id_from_current_course,
        file_id_from_a_different_course,
    ):
        # This is what happens when an instructor launches an assignment whose
        # file_id is *not* in the current course.

        # We *do* have a models.File object for the file_id in the DB, and its
        # name and size *do* match one of the files in the current course in Canvas.
        file_service.get.return_value = factories.File(
            name=file_from_current_course["display_name"],
            size=file_from_current_course["size"],
        )

        url = canvas_service.public_url_for_file(
            module_item_configuration,
            file_id_from_a_different_course,
            sentinel.course_id,
            check_in_course=True,
        )

        # check_in_course was True so it called list_files() to check whether
        # file_id was in the course.
        #
        # There's also a second call to list_files() because it calls it again
        # to look for a matching file in the current course. This does not make
        # two network requests because CanvasAPIClient.list_files() has
        # caching.
        assert canvas_api_client.list_files.call_args_list == [
            call(sentinel.course_id),
            call(sentinel.course_id),
        ]
        # It looks up the given file_id in the DB.
        file_service.get.assert_called_once_with(
            file_id_from_a_different_course, type_="canvas_file"
        )
        # It stores a file mapping from the given file_id to the matching
        # found_file_id so that it doesn't have to re-do the search the next
        # time the assignment is launched.
        assert (
            module_item_configuration.get_mapped_file_id(
                file_id_from_a_different_course
            )
            == file_id_from_current_course
        )
        # It calls public_url() with the found_file_id and returns the public URL.
        canvas_api_client.public_url.assert_called_once_with(
            file_id_from_current_course
        )
        assert url == canvas_api_client.public_url.return_value

    def test_file_not_found_in_course_but_no_file_info(
        self,
        canvas_service,
        module_item_configuration,
        file_service,
        file_id_from_a_different_course,
    ):
        # This is what happens when a teacher launches an assignment whose
        # file_id is *not* in the current course and we don't have a record of
        # the file_id in our DB.  Without a record we can't search for a
        # matching file so we raise an error.

        # There's no record of the file_id in the DB.
        file_service.get.return_value = None

        with pytest.raises(CanvasFileNotFoundInCourse):
            canvas_service.public_url_for_file(
                module_item_configuration,
                file_id_from_a_different_course,
                sentinel.course_id,
                check_in_course=True,
            )

    def test_file_not_found_in_course_but_no_matching_file(
        self,
        canvas_service,
        module_item_configuration,
        file_service,
        file_id_from_a_different_course,
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
            canvas_service.public_url_for_file(
                module_item_configuration,
                file_id_from_a_different_course,
                sentinel.course_id,
                check_in_course=True,
            )

    def test_permissions_error_and_matching_file_found(
        self,
        canvas_service,
        canvas_api_client,
        module_item_configuration,
        file_service,
        file_from_current_course,
        file_id_from_current_course,
        file_id_from_a_different_course,
    ):
        # This is what happens when a student launches an assignment whose
        # file_id is *not* in the current course.

        # The code is going to call public_url() twice. The first call is with
        # the original file_id and public_url() raises a permissions error. The
        # second call is with the matching found_file_id and public_url()
        # successfully returns a URL.
        canvas_api_client.public_url.side_effect = [CanvasAPIPermissionError, DEFAULT]

        # We *do* have a models.File object for the file_id in the DB, and its
        # name and size *do* match one of the files in the current course in Canvas.
        file_service.get.return_value = factories.File(
            name=file_from_current_course["display_name"],
            size=file_from_current_course["size"],
        )

        url = canvas_service.public_url_for_file(
            module_item_configuration,
            file_id_from_a_different_course,
            sentinel.course_id,
        )

        # It looks up the given file_id in the DB.
        file_service.get.assert_called_once_with(
            file_id_from_a_different_course, type_="canvas_file"
        )
        # It calls list_files() to look for a matching file in the current course.
        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)
        # It stores a file mapping from the given file_id to the matching
        # found_file_id so that it doesn't have to re-do the search the next
        # time the assignment is launched.
        assert (
            module_item_configuration.get_mapped_file_id(
                file_id_from_a_different_course
            )
            == file_id_from_current_course
        )
        # It calls public_url() twice: one with the original file_id and once
        # with the matching found_file_id.
        assert canvas_api_client.public_url.call_args_list == [
            call(file_id_from_a_different_course),
            call(file_id_from_current_course),
        ]
        # It returns the public URL of the file in the current course.
        assert url == canvas_api_client.public_url.return_value

    def test_permissions_error_but_no_file_info(
        self,
        canvas_service,
        canvas_api_client,
        module_item_configuration,
        file_service,
        file_id_from_a_different_course,
    ):
        # This is what happens when a student launches an assignment whose
        # file_id is *not* in the current course and we don't have a record of
        # the file_id in our DB. Without a record we can't search for a
        # matching file so we raise an error.
        canvas_api_client.public_url.side_effect = CanvasAPIPermissionError
        file_service.get.return_value = None

        with pytest.raises(CanvasAPIPermissionError):
            canvas_service.public_url_for_file(
                module_item_configuration,
                file_id_from_a_different_course,
                sentinel.course_id,
            )

    def test_permissions_error_but_no_matching_file(
        self,
        canvas_service,
        canvas_api_client,
        module_item_configuration,
        file_service,
        file_id_from_a_different_course,
    ):
        # This is what happens when a student launches an assignment whose
        # file_id is *not* in the current course and even though we do have a
        # record of this file_id in our DB we don't find a matching file in the
        # current course. Since we can't find a matching file we can't fix the
        # assignment so we raise an error.
        canvas_api_client.public_url.side_effect = CanvasAPIPermissionError

        # The file record that we find in our DB. Its name doesn't match any
        # file in the current course.
        file_service.get.return_value = factories.File(name="foo")

        with pytest.raises(CanvasAPIPermissionError):
            canvas_service.public_url_for_file(
                module_item_configuration,
                file_id_from_a_different_course,
                sentinel.course_id,
            )

    @pytest.fixture
    def module_item_configuration(self, db_session):
        module_item_configuration = factories.ModuleItemConfiguration()
        db_session.flush()
        return module_item_configuration

    @pytest.fixture
    def file_from_current_course(self, canvas_api_client):
        """Return the Canvas API file dict for a file that *is* in the current course."""
        return canvas_api_client.list_files.return_value[1]

    @pytest.fixture
    def file_id_from_current_course(self, file_from_current_course):
        """Return the ID of a file from the current course, as a string."""
        return str(file_from_current_course["id"])

    @pytest.fixture
    def file_from_a_different_course(self):
        """Return the Canvas API file dict for a file from a *different* course."""
        return {"id": 4, "display_name": "File 4", "size": 4096}

    @pytest.fixture
    def file_id_from_a_different_course(self, file_from_a_different_course):
        """Return the ID of a file from a *different* course, as a string."""
        return str(file_from_a_different_course["id"])


class TestAssertFileInCourse:
    def test_it_does_not_raise_if_the_file_is_in_the_course(self, canvas_service):
        canvas_service.assert_file_in_course("2", sentinel.course_id)

    def test_it_raises_if_the_file_isnt_in_the_course(self, canvas_service):
        with pytest.raises(CanvasFileNotFoundInCourse):
            canvas_service.assert_file_in_course("4", sentinel.course_id)


class TestFindMatchingFileInCourse:
    def test_it_returns_the_id_if_theres_a_matching_file_in_the_course(
        self, canvas_service, canvas_api_client
    ):
        # The file dict from the Canvas API that we expect the search to match.
        matching_file_dict = canvas_api_client.list_files.return_value[1]

        file_ = factories.File(
            name=matching_file_dict["display_name"],
            size=matching_file_dict["size"],
        )

        matching_file_id = canvas_service.find_matching_file_in_course(
            sentinel.course_id, file_
        )

        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)
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
    return CanvasService(canvas_api_client, file_service)


@pytest.fixture
def canvas_api_client(canvas_api_client):
    canvas_api_client.list_files.return_value = [
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
    return canvas_api_client
