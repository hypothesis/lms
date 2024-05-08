from enum import Enum

from lms.models import Course, Grouping
from lms.product.plugin.grouping import GroupError, GroupingPlugin
from lms.services.exceptions import ExternalRequestError
from lms.services.moodle import MoodleAPIClient


class ErrorCodes(str, Enum):
    """Error codes that the FE is going to check for."""

    GROUP_SET_NOT_FOUND = "moodle_group_set_not_found"
    GROUP_SET_EMPTY = "moodle_group_set_empty"
    STUDENT_NOT_IN_GROUP = "moodle_student_not_in_group"


class MoodleGroupingPlugin(GroupingPlugin):
    group_type = Grouping.Type.MOODLE_GROUP
    sections_type = None  # We don't support sections in Moodle

    def __init__(self, api, lti_user):
        self._api = api
        self._lti_user = lti_user

    def get_group_sets(self, course: Course):
        group_sets = self._api.course_group_sets(course.lms_id)
        course.set_group_sets(group_sets)
        return group_sets

    def get_groups_for_learner(self, _svc, course, group_set_id):
        try:
            if learner_groups := self._api.groups_for_user(
                course.lms_id, group_set_id, self._lti_user.user_id
            ):
                return learner_groups
        except ExternalRequestError as exc:
            if (
                exc.validation_errors
                # There are no error codes in Moodle's APIs
                and exc.validation_errors.get("errorcode") == "invalidrecord"
            ):
                raise GroupError(
                    ErrorCodes.GROUP_SET_NOT_FOUND, group_set=group_set_id
                ) from exc

            raise

        raise GroupError(ErrorCodes.STUDENT_NOT_IN_GROUP, group_set=group_set_id)

    def get_groups_for_grading(
        self,
        svc,  # noqa: ARG002
        course,
        group_set_id,
        grading_student_id=None,  # noqa: ARG002
    ):
        return self._api.groups_for_user(
            course.lms_id, group_set_id, grading_student_id
        )

    def get_groups_for_instructor(self, _svc, course, group_set_id):
        try:
            groups = self._api.group_set_groups(int(course.lms_id), group_set_id)
        except ExternalRequestError as exc:
            if (
                exc.validation_errors
                # There are no semantic HTTP error codes in Moodle's APIs
                and exc.validation_errors.get("errorcode") == "invalidrecord"
            ):
                raise GroupError(
                    ErrorCodes.GROUP_SET_NOT_FOUND, group_set=group_set_id
                ) from exc

            raise

        if not groups:
            raise GroupError(ErrorCodes.GROUP_SET_EMPTY, group_set=group_set_id)

        return groups

    @classmethod
    def factory(cls, _context, request):
        return cls(api=request.find_service(MoodleAPIClient), lti_user=request.lti_user)
