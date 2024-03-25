from lms.product.plugin.course_copy import CourseCopyFilesHelper, CourseCopyGroupsHelper
from lms.services.d2l_api import D2LAPIClient


class D2LCourseCopyPlugin:
    """Handle course copy for D2L."""

    file_type = "d2l_file"

    def __init__(
        self,
        api: D2LAPIClient,
        files_helper: CourseCopyFilesHelper,
        groups_helper: CourseCopyGroupsHelper,
    ):
        self._api = api
        self._files_helper = files_helper
        self._groups_helper = groups_helper

    def is_file_in_course(self, course_id, file_id):
        return self._files_helper.is_file_in_course(course_id, file_id, self.file_type)

    def find_matching_file_in_course(self, original_file_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.list_files, self.file_type, original_file_id, new_course_id
        )

    def find_matching_group_set_in_course(self, course, group_set_id):
        return self._groups_helper.find_matching_group_set_in_course(
            course, group_set_id
        )

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.find_service(name="d2l"),
            files_helper=request.find_service(CourseCopyFilesHelper),
            groups_helper=request.find_service(CourseCopyGroupsHelper),
        )
