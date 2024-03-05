from lms.product.plugin.course_copy import CourseCopyFilesHelper, CourseCopyGroupsHelper
from lms.services.moodle import MoodleAPIClient


class MoodleCourseCopyPlugin:
    file_type = "moodle_file"

    def __init__(
        self,
        api: MoodleAPIClient,
        groups_helper: CourseCopyGroupsHelper,
    ):
        self._api = api
        self._groups_helper = groups_helper

    def find_matching_group_set_in_course(self, course, group_set_id):
        return self._groups_helper.find_matching_group_set_in_course(
            course, group_set_id
        )

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.find_service(MoodleAPIClient),
            groups_helper=request.find_service(CourseCopyGroupsHelper),
        )
