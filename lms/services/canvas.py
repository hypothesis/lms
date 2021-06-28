from typing import Optional

from lms import models
from lms.services.exceptions import CanvasFileNotFoundInCourse


class CanvasService:
    """A high level Canvas service."""

    api = None

    def __init__(self, canvas_api):
        self.api = canvas_api

    def public_url_for_file(self, file_id, course_id, check_in_course=False):
        """
        Get a public URL for a Canvas file.

        This will also attempt to check if the file is in the course to detect
        course copy situations and fix it if we can.

        :param file_id: The file to look up
        :param course_id: The course the file should be in
        :param check_in_course: Raise CanvasFileNotFoundInCourse if file_id isn't in
            course_id
        :return: A URL suitable for public presentation of the file
        :raise  CanvasFileNotFoundInCourse: if check_in_course=True and file_id isn't in course_id
            be in the course but isn't.
        """

        if check_in_course:
            if not self.can_see_file_in_course(file_id, course_id):
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
    return CanvasService(canvas_api=request.find_service(name="canvas_api_client"))
