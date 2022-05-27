import json
from copy import deepcopy
from typing import Optional

from lms.models import Course, CourseGroupsExportedFromH, Grouping
from lms.services.grouping import GroupingService


class CourseService:
    def __init__(self, db, application_instance):
        self._db = db
        self._application_instance = application_instance

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
            .filter(Course.application_instance == self._application_instance)
            .filter(Course.settings[group][key] == json.dumps(value))
            .limit(1)
            .count()
        )

    def get_by_context_id(
        self, tool_consumer_instance_guid, context_id
    ) -> Optional[Course]:
        """
        Get a course (if one exists) by the GUID and context id.

        :param tool_consumer_instance_guid: The GUID from LTI params
        :param context_id: The course id from LTI params
        """
        authority_provided_id = self._get_authority_provided_id(
            tool_consumer_instance_guid, context_id
        )

        return self._get_by_authority_provided_id(authority_provided_id)

    # pylint: disable=too-many-arguments
    def upsert(
        self, tool_consumer_instance_guid, context_id, name, extra, settings=None
    ) -> Course:
        """
        Create or update a course based on the provided values.

        :param tool_consumer_instance_guid: The GUID from LTI params
        :param context_id: The course id from LTI params
        :param name: The name of the course
        :param extra: Additional LMS specific values
        :param settings: A dict of settings for the course
        """
        authority_provided_id = self._get_authority_provided_id(
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
    def _get_authority_provided_id(tool_consumer_instance_guid, context_id):
        """
        Generate the authority_provided_id based on the LTI params.

        These are "recommended" LTI parameters (according to the spec) that in
        practice are provided by all major LMS's.

         * `tool_consumer_instance_guid` uniquely identifies an LMS instance
         * `context_id uniquely` identifies a course within an LMS

        Together they  globally uniquely identify a course.
        """
        return GroupingService.generate_authority_provided_id(
            tool_consumer_instance_guid=tool_consumer_instance_guid,
            lms_id=context_id,
            parent=None,
            type_=Grouping.Type.COURSE,
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
        db=request.db,
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
    )
