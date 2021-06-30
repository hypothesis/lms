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
        mapped_file_id = module_item_configuration.get_canvas_mapped_file_id(file_id)

        # If there's a previously stored mapping for file_id use that instead.
        effective_file_id = mapped_file_id or file_id

        try:
            return self._public_url(
                effective_file_id,
                course_id=course_id if check_in_course else None,
            )
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
            file_ = self._file_service.get(effective_file_id, type_="canvas_file")

            if not file_:
                # We don't have a record of the assignment's file in our DB.
                # This can happen, for example, if Hypothesis has not been
                # launched in the original assignment's course since we
                # deployed the code that started recording files in the DB.
                raise

            # Look for a copy of the assignment's file that the current user
            # *can* see in the current course.
            found_file_id = self.find_matching_file_in_course(course_id, file_)

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
            return self._public_url(found_file_id)

    def _public_url(self, file_id, course_id=None):
        if course_id and not self.can_see_file_in_course(file_id, course_id):
            raise CanvasFileNotFoundInCourse(file_id)

        return self.api.public_url(file_id)

    def can_see_file_in_course(self, file_id: str, course_id: str) -> bool:
        """
        Return True if the current user can see file_id in course_id.

        Return False if the current user cannot currently see a file with ID
        file_id in the course with ID course_id. This could be because the file
        is in another course, because the file was in course_id but has been
        deleted, or because the file is in course_id but the current user
        doesn't have permission to see it (for example files that are marked as
        "unpublished" in Canvas can only be seen by teachers, not students).
        """
        files_in_course = self.api.list_files(course_id)

        for file_ in files_in_course:

            # The Canvas API returns file IDs as ints but the file_id param
            # that this method receives (from our proxy API) is a string.
            # Convert ints to strings so that we can compare them.
            if str(file_["id"]) == file_id:
                return True

        return False

    def find_matching_file_in_course(
        self, course_id: str, file_: models.File
    ) -> Optional[str]:
        """
        Return the ID of a file in course_id that matches file_.

        Search for a file that the current Canvas user can see in course_id and
        that matches the given file_ (same filename and size) and return the
        matching file's ID.

        Return None if no matching file is found.
        """
        file_dicts = self.api.list_files(course_id)

        for file_dict in file_dicts:
            display_name = file_dict["display_name"]
            size = file_dict["size"]

            if display_name == file_.name and size == file_.size:
                return str(file_dict["id"])

        return None


def factory(_context, request):
    return CanvasService(
        canvas_api=request.find_service(name="canvas_api_client"),
        file_service=request.find_service(name="file"),
    )
