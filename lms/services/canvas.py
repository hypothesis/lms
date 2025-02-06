from lms.services.canvas_api.client import CanvasAPIClient
from lms.services.exceptions import CanvasAPIPermissionError, FileNotFoundInCourse


class CanvasService:
    """A high level Canvas service."""

    api: CanvasAPIClient = None  # type:ignore  # noqa: PGH003

    def __init__(self, canvas_api, course_copy_plugin):
        self.api = canvas_api
        self._course_copy_plugin = course_copy_plugin

    def public_url_for_file(
        self,
        assignment,
        file_id,
        current_course_id,
        check_in_course=False,  # noqa: FBT002
    ):
        """
        Return a public URL for file_id.

        :param assignment: the current assignment
        :param file_id: the Canvas API ID of the file
        :param current_course_id: the Canvas API ID of the current course
        :param check_in_course: whether to check that file_id is in course_id

        :raise FileNotFoundInCourse: if check_in_course was True and the
            current user can't see file_id in course_id's list of files

        :raise CanvasAPIPermissionError: if the user gets a permissions error
            from the Canvas API when trying to get a public URL for file_id
        """
        # If there's a previously stored mapping for file_id use that instead.
        effective_file_id = assignment.get_canvas_mapped_file_id(file_id)
        try:
            if check_in_course:  # noqa: SIM102
                if not self._course_copy_plugin.is_file_in_course(
                    current_course_id, effective_file_id
                ):
                    raise FileNotFoundInCourse(  # noqa: TRY301
                        "canvas_file_not_found_in_course",
                        file_id,
                    )
            return self.api.public_url(effective_file_id)
        except (FileNotFoundInCourse, CanvasAPIPermissionError):
            # The user can't see the file in the course. This could be because:
            #
            # * The course has been copied so the assignment's file_id is from
            #   the original course (and the user isn't in the original course)
            # * The assignment's file has been deleted from Canvas
            # * The file *is* in the course but the user can't see it
            #   (only instructors can see "unpublished" files in Canvas)
            #
            # We'll try to find another copy of the same file that the current
            # user *can* see in the current course and use that instead.
            found_file_id = self._course_copy_plugin.find_matching_file_in_course(
                current_course_id,
                # Use a set to avoid searching for the same ID twice if file_id
                # and effective_file_id are the same.
                {file_id, effective_file_id},
            )

            if not found_file_id:
                raise

            # Try again to return a public URL, this time using found_file_id.
            url = self.api.public_url(found_file_id)

            # Store a mapping so we don't have to re-search next time.
            assignment.set_canvas_mapped_file_id(file_id, found_file_id)

            return url


def factory(_context, request):
    return CanvasService(
        canvas_api=request.find_service(name="canvas_api_client"),
        course_copy_plugin=request.product.plugin.course_copy,
    )
