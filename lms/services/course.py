import json
from copy import deepcopy
from typing import Optional

from lms.models import Course, CourseGroupsExportedFromH, Grouping
from lms.services.grouping import GroupingService


class CourseService:
    def __init__(self, db, application_instance, grouping_service: GroupingService):
        self._db = db
        self._application_instance = application_instance
        self._grouping_service = grouping_service

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

    def get_by_context_id(self, context_id) -> Optional[Course]:
        """
        Get a course (if one exists) by the GUID and context id.

        :param context_id: The course id from LTI params
        """

        return (
            self._db.query(Course)
            .filter_by(
                application_instance=self._application_instance,
                authority_provided_id=self._get_authority_provided_id(context_id),
            )
            .one_or_none()
        )

    def upsert_course(self, context_id, name, extra) -> Course:
        """
        Create or update a course based on the provided values.

        :param context_id: The course id from LTI params
        :param name: The name of the course
        :param extra: Additional LMS specific values
        """

        settings = self._new_course_settings(
            settings=deepcopy(self._application_instance.settings),
            authority_provided_id=self._get_authority_provided_id(context_id),
        )

        return self._grouping_service.upsert_groupings(
            [
                {
                    "lms_id": context_id,
                    "lms_name": name,
                    "extra": extra,
                    "settings": settings,
                }
            ],
            type_=Grouping.Type.COURSE,
        )[0]

    def _get_authority_provided_id(self, context_id):
        return self._grouping_service.get_authority_provided_id(
            lms_id=context_id, type_=Grouping.Type.COURSE
        )

    def _new_course_settings(self, settings, authority_provided_id):
        # If the group was pre-sections, and we've just seen it for the first
        # time, turn sections off
        if self._db.query(CourseGroupsExportedFromH).get(authority_provided_id):
            settings.set("canvas", "sections_enabled", False)

        return settings


def course_service_factory(_context, request):
    return CourseService(
        db=request.db,
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        grouping_service=request.find_service(name="grouping"),
    )
