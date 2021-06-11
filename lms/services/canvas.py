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
        :param check_in_course: Enable pre-emptive checking for the file in the
            course regardless of whether the user has permission to see it
        :return: A URL suitable for public presentation of the file
        :raises  CanvasFileNotFoundInCourse: If we determine the file should
            be in the course but isn't.
        """

        if check_in_course:
            if not self._file_in_course(file_id, course_id):
                # Looks like a course copy
                raise CanvasFileNotFoundInCourse(file_id)

        return self.api.public_url(file_id)

    def _file_in_course(self, file_id, course_id):
        return any(
            str(file_["id"]) == str(file_id) for file_ in self.api.list_files(course_id)
        )


def factory(_context, request):
    return CanvasService(canvas_api=request.find_service(name="canvas_api_client"))
