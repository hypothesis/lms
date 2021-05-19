from lms.models._hashed_id import hashed_id


class GroupingService:
    def __init__(self, db, course_service):
        self._db = db
        self._course_service = course_service

    def course_grouping(
        self,
        tool_consumer_instance_guid,
        course_name,
        context_id,
        extra=None,
    ):
        """
        Get / update / create a Grouping for a course.

        :param tool_consumer_instance_guid: Tool consumer GUID
        :param course_name: The name of the course
        :param context_id: Course id on the LMS
        :param extra: Any other extra information of the course
        """
        authority_provided_id = hashed_id(tool_consumer_instance_guid, context_id)

        # As courses are found in both Grouping and the old `course` table
        # we don't handle the upsert logic here, course_service will get or crate a row in the new table
        course = self._course_service.get_or_create(
            authority_provided_id, context_id, course_name, extra
        )
        # Update some fields that might have changed
        course.lms_name = course_name

        return course


def factory(_context, request):
    return GroupingService(
        request.db,
        request.find_service(name="course"),
    )
