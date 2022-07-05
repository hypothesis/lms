# pylint: disable=unused-argument
from lms.models import ApplicationSettings


class CourseServicePlugin:  # pragma: nocover
    def get_new_course_settings(
        self, settings: ApplicationSettings, authority_provided_id
    ) -> ApplicationSettings:
        """Get settings for a new course."""

        return settings

    def get_new_course_extra(self) -> dict:
        """Get extra dict for a new course."""

        return {}
