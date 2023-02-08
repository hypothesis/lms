from lms.product.plugin.course_copy import CourseCopyFilesHelper
from lms.services.d2l_api import D2LAPIClient


class D2LCourseCopyPlugin:
    """Handle course copy for D2L."""

    file_type = "d2l_file"

    def __init__(
        self,
        api: D2LAPIClient,
        files_helper: CourseCopyFilesHelper,
    ):
        self._api = api
        self._files_helper = files_helper

    def is_file_in_course(self, course_id, file_id):
        return self._files_helper.is_file_in_course(course_id, file_id, self.file_type)

    def find_matching_file_in_course(self, original_file_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.list_files, self.file_type, original_file_id, new_course_id
        )

    def get_mapped_file_id(self, course, file_id):
        return self._files_helper.get_mapped_file_id(course, file_id)

    def set_mapped_file_id(self, course, old_file_id, new_file_id):
        self._files_helper.set_mapped_file_id(course, old_file_id, new_file_id)

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.find_service(D2LAPIClient),
            files_helper=request.find_service(CourseCopyFilesHelper),
        )
