from lms.models import Course, CourseGroupsExportedFromH


class CourseService:
    def __init__(self, ai_getter, consumer_key, db):
        self._ai_getter = ai_getter
        self._consumer_key = consumer_key
        self._db = db

    def get_or_create(self, authority_provided_id):
        """Add the current course to the `course` table if it's not there already."""
        return self._get(authority_provided_id) or self._create(authority_provided_id)

    def _get(self, authority_provided_id):
        return self._db.query(Course).get((self._consumer_key, authority_provided_id))

    def _create(self, authority_provided_id):
        # This is weird I feel the thing we get back kind of should do it all
        app_instance = self._ai_getter.get()
        if not app_instance:
            # Should we raise here?
            return

        settings = app_instance.settings

        if (
            self._ai_getter.canvas_sections_supported()
            and settings.get("canvas", "sections_enabled")
            and self._is_pre_sections(authority_provided_id)
        ):
            settings.set("canvas", "sections_enabled", False)

        course = Course(
            consumer_key=self._consumer_key,
            authority_provided_id=authority_provided_id,
            _settings=settings.data,
        )

        self._db.add(course)

        return course

    def _is_pre_sections(self, authority_provided_id):
        return bool(
            self._db.query(CourseGroupsExportedFromH).get(authority_provided_id)
        )


def course_service_factory(_context, request):
    return CourseService(
        request.find_service(name="ai_getter"),
        request.lti_user.oauth_consumer_key,
        request.db,
    )
