from lms.models import ApplicationSettings, CourseGroupsExportedFromH
from lms.product.plugin.course_service import CourseServicePlugin


class CanvasCoursePlugin(CourseServicePlugin):
    def __init__(self, db_session, parsed_params):
        self._db_session = db_session
        self._parsed_params = parsed_params

    def get_new_course_settings(
        self, settings: ApplicationSettings, authority_provided_id
    ) -> ApplicationSettings:
        # Disable sections for courses which existed before sections but we
        # haven't seen since
        if self._db_session.query(CourseGroupsExportedFromH).get(authority_provided_id):
            settings.set("canvas", "sections_enabled", False)

        return settings

    def get_new_course_extra(self) -> dict:
        return {
            "canvas": {
                "custom_canvas_course_id": self._parsed_params.get(
                    "custom_canvas_course_id"
                )
            }
        }

    @classmethod
    def factory(cls, _context, request):
        return cls(db_session=request.db, parsed_params=request.parsed_params)
