import json
from copy import deepcopy

from lms.models import Course, CourseGroupsExportedFromH


class CourseService:
    def __init__(self, application_instance, consumer_key, db):
        self._application_instance = application_instance
        self._consumer_key = consumer_key
        self._db = db

    def get_or_create(self, authority_provided_id):
        """Add the current course to the `course` table if it's not there already."""
        return self._get(authority_provided_id) or self._create(authority_provided_id)

    def any_with_setting(self, group, key, value=True):
        """
        Return whether any course has the specified setting.

        Note! This will only work for courses that have the key and the value,
        so if the key is missing entirely it will not be counted.

        :param group: Setting group name
        :param key: Setting key
        :param value: Expected value
        """

        return bool(
            self._db.query(Course)
            .filter(Course.consumer_key == self._consumer_key)
            .filter(Course.settings[group][key] == json.dumps(value))
            .limit(1)
            .count()
        )

    def _get(self, authority_provided_id):
        return self._db.query(Course).get((self._consumer_key, authority_provided_id))

    def _create(self, authority_provided_id):
        # By default we'll make our course setting have the same settings
        # as the application instance
        course_settings = deepcopy(self._application_instance.settings)

        # Unless! The group was pre-sections, and we've just seen it for the
        # first time in which case turn sections off
        if course_settings.get("canvas", "sections_enabled") and self._is_pre_sections(
            authority_provided_id
        ):
            course_settings.set("canvas", "sections_enabled", False)

        course = Course(
            consumer_key=self._consumer_key,
            authority_provided_id=authority_provided_id,
            settings=course_settings,
        )

        self._db.add(course)

        return course

    def _is_pre_sections(self, authority_provided_id):
        return bool(
            self._db.query(CourseGroupsExportedFromH).get(authority_provided_id)
        )


def course_service_factory(_context, request):
    return CourseService(
        request.find_service(name="application_instance").get(),
        request.lti_user.oauth_consumer_key,
        request.db,
    )
