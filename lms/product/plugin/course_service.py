# pylint: disable=unused-argument
from lms.models import ApplicationSettings


class CourseServicePlugin:  # pragma: nocover
    def get_new_course_settings(
        self, settings: ApplicationSettings, authority_provided_id
    ) -> ApplicationSettings:
        """Get settings for a new course."""

        return settings

    def get_course_extras(self) -> dict:
        """Get extra dict for when upserting courses."""

        return {}
