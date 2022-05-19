import json
from copy import deepcopy

from lms.models import Course, CourseGroupsExportedFromH, Grouping
from lms.services.grouping import GroupingService


class CourseService:
    def __init__(self, application_instance_service, db):
        self._application_instance = application_instance_service.get_current()
        self._db = db

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
            .filter(Course.application_instance == self._application_instance)
            .filter(Course.settings[group][key] == json.dumps(value))
            .limit(1)
            .count()
        )

    def get(self, tool_consumer_instance_guid, context_id):
        authority_provided_id = self._generate_authority_provided_id(
            tool_consumer_instance_guid, context_id
        )

        return self._get_by_authority_provided_id(authority_provided_id)

    def upsert(
        self, tool_consumer_instance_guid, context_id, name, extra, settings=None
    ):  # pylint: disable=too-many-arguments
        authority_provided_id = self._generate_authority_provided_id(
            tool_consumer_instance_guid, context_id
        )

        course = self._get_by_authority_provided_id(authority_provided_id)
        if not course:
            course = Course(
                application_instance_id=self._application_instance.id,
                authority_provided_id=authority_provided_id,
                lms_id=context_id,
                lms_name=name,
                settings=settings or self._new_course_settings(authority_provided_id),
                extra=extra,
            )
            self._db.add(course)

        # Update any values that might have changed
        course.lms_name = name
        course.extra = extra

        return course

    @staticmethod
    def _generate_authority_provided_id(tool_consumer_instance_guid, context_id):
        """
        Generate the authority_provided_id based on the LTI  tool_consumer_instance_guid and context_id parameters.

        These are "recommended" LTI parameters (according to the spec) that in
        practice are provided by all of the major LMS's.
        tool_consumer_instance_guid uniquely identifies an instance of an LMS,
        and context_id uniquely identifies a course within an LMS. Together they
        globally uniquely identify a course.
        """
        return GroupingService.generate_authority_provided_id(
            tool_consumer_instance_guid, context_id, None, Grouping.Type.COURSE
        )

    def _get_by_authority_provided_id(self, authority_provided_id):
        return (
            self._db.query(Course)
            .filter_by(
                application_instance=self._application_instance,
                authority_provided_id=authority_provided_id,
            )
            .one_or_none()
        )

    def _new_course_settings(self, authority_provided_id):
        # By default we'll make our course setting have the same settings
        # as the application instance
        course_settings = deepcopy(self._application_instance.settings)

        # Unless! The group was pre-sections, and we've just seen it for the
        # first time in which case turn sections off
        if course_settings.get("canvas", "sections_enabled") and self._is_pre_sections(
            authority_provided_id
        ):
            course_settings.set("canvas", "sections_enabled", False)

        return course_settings

    def _is_pre_sections(self, authority_provided_id):
        return bool(
            self._db.query(CourseGroupsExportedFromH).get(authority_provided_id)
        )


def course_service_factory(_context, request):
    return CourseService(
        request.find_service(name="application_instance"),
        request.db,
    )
