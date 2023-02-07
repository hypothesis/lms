from lms.product.plugin.course_copy import CourseCopyFilesHelper, CourseCopyGroupsHelper
from lms.services.file import FileService


class BlackboardCourseCopyPlugin:
    """Handle course copy for Blackboard."""

    file_type = "blackboard_file"

    def __init__(
        self,
        api,
        file_service: FileService,
        files_helper: CourseCopyFilesHelper,
        groups_helper: CourseCopyGroupsHelper,
    ):
        self._api = api
        self._file_service = file_service
        self._files_helper = files_helper
        self._groups_helper = groups_helper

    def is_file_in_course(self, course_id, file_id):
        return self._files_helper.is_file_in_course(
            self._file_service, course_id, file_id, self.file_type
        )

    def find_matching_file_in_course(self, original_file_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.list_all_files,
            self._file_service,
            self.file_type,
            original_file_id,
            new_course_id,
        )

    def find_matching_group_set_in_course(self, course, group_set_id):
        return self._groups_helper.find_matching_group_set_in_course(
            course, group_set_id
        )

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.find_service(name="blackboard_api_client"),
            file_service=request.find_service(name="file"),
            files_helper=CourseCopyFilesHelper(),
            groups_helper=request.find_service(CourseCopyGroupsHelper),
        )
