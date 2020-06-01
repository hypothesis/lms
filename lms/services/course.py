from lms.models import Course, CourseGroupsExportedFromH


class CourseService:
    def __init__(self, ai_getter, consumer_key, db):
        self._ai_getter = ai_getter
        self._consumer_key = consumer_key
        self._db = db

    def record(self, authority_provided_id):
        """Add the current course to the `course` table if it's not there already."""
        sections_enabled = self._ai_getter.canvas_sections_enabled()

        existing_course = self._db.query(Course).get(
            (self._consumer_key, authority_provided_id)
        )
        if existing_course:
            return

        if sections_enabled:
            course_group = self._db.query(CourseGroupsExportedFromH).get(
                authority_provided_id
            )
            if course_group:
                sections_enabled = False

        self._db.add(
            Course(
                consumer_key=self._consumer_key,
                authority_provided_id=authority_provided_id,
                _settings={"canvas": {"sections_enabled": sections_enabled}},
            )
        )


def course_service_factory(_context, request):
    return CourseService(
        request.find_service(name="ai_getter"),
        request.lti_user.oauth_consumer_key,
        request.db,
    )
