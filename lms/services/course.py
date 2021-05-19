import json
from copy import deepcopy

from lms.models import Course, CourseGroupsExportedFromH
from lms.models import _Course as LegacyCourse


class CourseService:
    def __init__(self, application_instance_service, consumer_key, db):
        self._application_instance = application_instance_service.get()
        self._consumer_key = consumer_key
        self._db = db

    def get_or_create(self, authority_provided_id, context_id, name, extra=None):
        """Add the current course to the `course` table if it's not there already."""
        return self._get(
            authority_provided_id, context_id, name, extra
        ) or self._create(authority_provided_id, context_id, name, extra)

    def any_with_setting(self, group, key, value=True) -> bool:
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
            .filter(Course.application_instance_id == self._application_instance.id)
            .filter(Course.settings[group][key] == json.dumps(value))
            .limit(1)
            .count()
        ) or bool(
            self._db.query(LegacyCourse)
            .filter(LegacyCourse.consumer_key == self._consumer_key)
            .filter(LegacyCourse.settings[group][key] == json.dumps(value))
            .limit(1)
            .count()
        )

    def _get(self, authority_provided_id, context_id, name, extra):
        """
        Get a Course from Course and fallback to rows on LegacyCourse.

        We are moving rows from LegacyCourse to Course so this method could potentially
        create a new row in Course and delete the existing one on LegacyCourse,
        that the reason it needs all the information of the course (context_id, name...) despite being called `_get`.
        """
        # Let's try first on the new table
        course = (
            self._db.query(Course)
            .filter_by(
                application_instance_id=self._application_instance.id,
                authority_provided_id=authority_provided_id,
            )
            .one_or_none()
        )
        if course:
            return course

        # Fall-back to the old table
        legacy_course = self._db.query(LegacyCourse).get(
            (self._consumer_key, authority_provided_id)
        )
        if legacy_course:
            # We have a record on the old, table, create one in the new one
            course = self._create(authority_provided_id, context_id, name, extra)
            # And delete the old one
            self._db.delete(legacy_course)

            return course

        # First time we've seen this course, create it on the new table directly
        return self._create(authority_provided_id, context_id, name, extra)

    def _create(self, authority_provided_id, context_id, name, extra):
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
            application_instance_id=self._application_instance.id,
            authority_provided_id=authority_provided_id,
            lms_id=context_id,
            lms_name=name,
            settings=course_settings,
            extra=extra,
        )

        self._db.add(course)

        return course

    def _is_pre_sections(self, authority_provided_id):
        return bool(
            self._db.query(CourseGroupsExportedFromH).get(authority_provided_id)
        )


def course_service_factory(_context, request):
    return CourseService(
        request.find_service(name="application_instance"),
        request.lti_user.oauth_consumer_key,
        request.db,
    )
