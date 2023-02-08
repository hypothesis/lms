from lms.product.plugin.course_copy import CourseCopyFilesHelper


class BlackboardCourseCopyPlugin:
    """Handle course copy for Blackboard."""

    file_type = "blackboard_file"

    def __init__(self, api, files_helper: CourseCopyFilesHelper):
        self._api = api
        self._files_helper = files_helper

    def is_file_in_course(self, course_id, file_id):
        return self._files_helper.is_file_in_course(course_id, file_id, self.file_type)

    def find_matching_file_in_course(self, original_file_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.list_all_files, self.file_type, original_file_id, new_course_id
        )

    def get_mapped_file_id(self, course, file_id):
        return self._files_helper.get_mapped_file_id(course, file_id)

    def set_mapped_file_id(self, course, old_file_id, new_file_id):
        self._files_helper.set_mapped_file_id(course, old_file_id, new_file_id)

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.find_service(name="blackboard_api_client"),
            request.find_service(CourseCopyFilesHelper),
        )
