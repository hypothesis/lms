from lms.models import CanvasSection, Grouping
from lms.models._hashed_id import hashed_id


class GroupingService:
    def __init__(self, db, application_instance_service, course_service):
        self._db = db
        self._application_instance = application_instance_service.get()
        self._course_service = course_service

    def upsert(self, grouping):
        db_grouping = (
            self._db.query(Grouping)
            .filter_by(
                application_instance_id=grouping.application_instance.id,
                authority_provided_id=grouping.authority_provided_id,
                type=grouping.type,
            )
            .one_or_none()
        )
        if not db_grouping:
            self._db.add(grouping)
        else:
            # Update any fields that might have changed
            db_grouping.lms_name = grouping.name

        return db_grouping or grouping

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

    def section_grouping(
        self, tool_consumer_instance_guid, context_id, section_id, section_name
    ):
        """
        Create an HGroup for a course section.

        :param section_name: The name of the section
        :param tool_consumer_instance_guid: Tool consumer GUID
        :param context_id: Course id the section is a part of
        :param section_id: A section id for a section group
        """

        section_authority_provided_id = hashed_id(
            tool_consumer_instance_guid, context_id, section_id
        )

        course_authority_provided_id = hashed_id(
            tool_consumer_instance_guid, context_id
        )

        course = self._course_service.get_or_create(
            course_authority_provided_id, context_id, None, None
        )

        return self.upsert(
            CanvasSection(
                application_instance_id=self._application_instance.id,
                authority_provided_id=section_authority_provided_id,
                lms_id=section_id,
                lms_name=section_name,
                parent_id=course.id,
            )
        )


def factory(_context, request):
    return GroupingService(
        request.db,
        request.find_service(name="application_instance"),
        request.find_service(name="course"),
    )
