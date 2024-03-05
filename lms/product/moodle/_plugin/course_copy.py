from lms.product.plugin.course_copy import CourseCopyFilesHelper, CourseCopyGroupsHelper
from lms.services.moodle import MoodleAPIClient


class MoodleCourseCopyPlugin:
    file_type = "moodle_file"
    page_type = "moodle_page"

    def __init__(
        self,
        api: MoodleAPIClient,
        files_helper: CourseCopyFilesHelper,
        groups_helper: CourseCopyGroupsHelper,
    ):
        self._api = api
        self._groups_helper = groups_helper
        self._files_helper = files_helper

    def find_matching_file_in_course(self, original_file_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.list_files, self.file_type, original_file_id, new_course_id
        )

    def find_matching_page_in_course(self, original_page_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.list_pages, self.page_type, original_page_id, new_course_id
        )

    def find_matching_group_set_in_course(self, course, group_set_id):
        return self._groups_helper.find_matching_group_set_in_course(
            course, group_set_id
        )

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.find_service(MoodleAPIClient),
            files_helper=request.find_service(CourseCopyFilesHelper),
            groups_helper=request.find_service(CourseCopyGroupsHelper),
        )
