from lms.product.plugin.course_copy import CourseCopyPlugin
from lms.services.d2l_api import D2LAPIClient
from lms.services.exceptions import CanvasFileNotFoundInCourse


class D2LCourseCopyPlugin(CourseCopyPlugin):
    """
        select application_instance_id, type, lms_id, count(*) from file where type in ('blackboard_file', 'blackboard_folder')
    group by application_instance_id, type, lms_id
    """

    file_type = "d2l_file"
    folder_type = "d2l_folder"

    def __init__(self, db, api, file_service):
        self._db = db
        self._api = api
        self._file_service = file_service

    def assert_file_in_course(self, course_id, file_id):
        """Raise if the current user can't see file_id in course_id."""
        original_file = self._file_service.get(file_id, type_=self.file_type)
        if not original_file or original_file.course_id != course_id:
            raise CanvasFileNotFoundInCourse(file_id)

    def _store_new_course_files(self, course_id):
        return self._api.list_files(course_id)

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.db,
            request.find_service(D2LAPIClient),
            file_service=request.find_service(name="file"),
        )
