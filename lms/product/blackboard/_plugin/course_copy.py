from lms.product.plugin.course_copy import CourseCopyPlugin


class BlackboardCourseCopyPlugin(CourseCopyPlugin):
    """
        select application_instance_id, type, lms_id, count(*) from file where type in ('blackboard_file', 'blackboard_folder')
    group by application_instance_id, type, lms_id
    """

    file_type = "blackboard_file"
    folder_type = "blackboard_folder"

    def __init__(self, db, api, file_service):
        self._db = db
        self._api = api
        self._file_service = file_service

    def _store_new_course_files(self, course_id):
        return self._api.list_all_files(course_id)

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.db,
            request.find_service(name="blackboard_api_client"),
            file_service=request.find_service(name="file"),
        )
