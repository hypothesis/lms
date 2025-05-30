from lms.product.plugin.course_copy import CourseCopyFilesHelper, CourseCopyGroupsHelper
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError


class CanvasCourseCopyPlugin:
    """Handle course copy in Canvas."""

    file_type = "canvas_file"
    page_type = "canvas_page"

    def __init__(
        self,
        api,
        file_service,
        files_helper: CourseCopyFilesHelper,
        groups_helper: CourseCopyGroupsHelper,
    ):
        self._api = api
        self._file_service = file_service
        self._files_helper = files_helper
        self._groups_helper = groups_helper

    def is_file_in_course(self, course_id, file_id):
        return self._files_helper.is_file_in_course(course_id, file_id, self.file_type)

    def find_matching_file_in_course(self, current_course_id, file_ids) -> str | None:
        """
        Return the ID of a file in course_id that matches one of the files in file_ids.

        Search for a file that the current Canvas user can see in course_id and
        that matches one of the files in file_id's (same filename and size) and
        return the matching file's ID.

        Return None if no matching file is found.
        """
        try:
            # Find the files in the current course. We call this for the side effect of storing the files in the DB
            _ = self._api.list_files(current_course_id)

        except OAuth2TokenError:
            # If the issue while trying to talk to the API is OAuth related
            # let that bubble up and be dealt with.
            raise

        except ExternalRequestError:
            # We might not have access to use the API for that endpoint.
            # That will depend on our role and the course's permissions settings.
            # We will continue anyway, maybe the files of the new course are already in the DB
            # after an instructor launch corrected the issue.
            pass

        for file_id in file_ids:
            file = self._file_service.get(file_id, type_=self.file_type)

            if not file:
                continue

            if new_file := self._file_service.find_copied_file(current_course_id, file):
                return new_file.lms_id

        return None

    def find_matching_page_in_course(self, original_page_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.pages.list, self.page_type, original_page_id, new_course_id
        )

    def find_matching_group_set_in_course(self, course, group_set_id):
        return self._groups_helper.find_matching_group_set_in_course(
            course, group_set_id
        )

    @classmethod
    def factory(cls, _context, request):
        return cls(
            api=request.find_service(name="canvas_api_client"),
            file_service=request.find_service(name="file"),
            files_helper=request.find_service(CourseCopyFilesHelper),
            groups_helper=request.find_service(CourseCopyGroupsHelper),
        )
