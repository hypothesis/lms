from typing import Optional

from lms import models
from lms.services.exceptions import CanvasAPIPermissionError, CanvasFileNotFoundInCourse


class CanvasService:
    """A high level Canvas service."""

    api = None

    def __init__(self, canvas_api, file_service):
        self.api = canvas_api
        self._file_service = file_service

    def public_url_for_file(
        self, module_item_configuration, file_id, course_id, check_in_course=False
    ):
        """
        Return a public URL for file_id.

        :param module_item_configuration: the ModuleItemConfiguration for the
            current assignment
        :param file_id: the Canvas API ID of the file
        :param course_id: the Canvas API ID of the course that the file is in
        :param check_in_course: whether to check that file_id is in course_id

        :raise CanvasFileNotFoundInCourse: if check_in_course was True and the
            current user can't see file_id in course_id's list of files

        :raise CanvasAPIPermissionError: if the user gets a permissions error
            from the Canvas API when trying to get a public URL for file_id
        """

        mapped_file_id = module_item_configuration.get_canvas_mapped_file_id(file_id)

        # If there's a previously stored mapping for file_id use that instead.
        effective_file_id = mapped_file_id or file_id

        try:
            if check_in_course:
                self.assert_file_in_course(effective_file_id, course_id)
            return self.api.public_url(effective_file_id)
        except (CanvasFileNotFoundInCourse, CanvasAPIPermissionError):
            # Either the user can't see the file in the current course's list
            # of files or the user got a permissions error from the Canvas API
            # when trying to get a public URL for the file.
            #
            # This can happen because the course has been copied and the
            # assignment's file_id is from the original course. Or it can
            # happen because the assignment's file has been deleted from
            # Canvas. Or it can happen because the user doesn't have permission
            # to see the file ("unpublished" files in Canvas are visible to
            # instructors but not to students).
            #
            # We'll try to find another copy of the same file that the current
            # user *can* see in the current course and use that instead.

            # Look for a previously saved record of the assignment's file in our DB.
            file = self._file_service.get(effective_file_id, type_="canvas_file")

            if not file:
                # We don't have a record of the assignment's file in our DB.
                # This can happen, for example, if Hypothesis has not been
                # launched in the original assignment's course since we
                # deployed the code that started recording files in the DB.
                raise

            # Look for a copy of the assignment's file that the current user
            # *can* see in the current course.
            found_file_id = self.find_matching_file_in_course(course_id, file)

            if not found_file_id:
                # We didn't find a matching file in the current course.
                # This could mean that the file has been deleted, has been
                # renamed, or the current user doesn't have permission to see
                # the file.
                raise

            # We found a matching copy of the assignment's file that the
            # current user *can* see in the current course. Store a mapping so
            # that we don't have to re-do the search the next time the
            # assignment is launched.
            module_item_configuration.set_canvas_mapped_file_id(file_id, found_file_id)

            # Try again using the found matching file.
            return self.api.public_url(found_file_id)

    def assert_file_in_course(self, file_id: str, course_id: str) -> bool:
        """
        Raise if the current user can't see file_id in course_id.

        Raise CanvasFileNotFoundInCourse if the current user can't see a file
        with ID file_id in the course with ID course_id. This could be because
        the file is in another course, because the file was in course_id but
        has been deleted, or because the file is in course_id but the current
        user doesn't have permission to see it (for example files that are
        marked as "unpublished" in Canvas can only be seen by teachers, not
        students).
        """
        for file in self.api.list_files(course_id):
            # The Canvas API returns file IDs as ints but the file_id param
            # that this method receives (from our proxy API) is a string.
            # Convert ints to strings so that we can compare them.
            if str(file["id"]) == file_id:
                return

        raise CanvasFileNotFoundInCourse(file_id)

    def find_matching_file_in_course(
        self, course_id: str, file: models.File
    ) -> Optional[str]:
        """
        Return the ID of a file in course_id that matches `file`.

        Search for a file that the current Canvas user can see in course_id and
        that matches the given `file` (same filename and size) and return the
        matching file's ID.

        Return None if no matching file is found.
        """
        file_dicts = self.api.list_files(course_id)

        for file_dict in file_dicts:
            display_name = file_dict["display_name"]
            size = file_dict["size"]

            if display_name == file.name and size == file.size:
                return str(file_dict["id"])

        return None


def factory(_context, request):
    return CanvasService(
        canvas_api=request.find_service(name="canvas_api_client"),
        file_service=request.find_service(name="file"),
    )
