from enum import Enum

from lms.models import Grouping
from lms.services.exceptions import ExternalRequestError
from lms.services.grouping.plugin import GroupError, GroupingServicePlugin


class ErrorCodes(str, Enum):
    """Error codes that the FE is going to check for."""

    GROUP_SET_NOT_FOUND = "blackboard_group_set_not_found"
    GROUP_SET_EMPTY = "blackboard_group_set_empty"
    STUDENT_NOT_IN_GROUP = "blackboard_student_not_in_group"


class BlackboardGroupingPlugin(GroupingServicePlugin):
    """A plugin which implements Blackboard specific grouping functions."""

    group_type = Grouping.Type.BLACKBOARD_GROUP
    sections_type = None  # We don't support sections in Blackboard

    def __init__(self, blackboard_api):
        self._blackboard_api = blackboard_api

    def get_groups_for_learner(self, _svc, course, group_set_id):
        if learner_groups := self._blackboard_api.course_groups(
            course.lms_id, group_set_id, current_student_own_groups_only=True
        ):
            return learner_groups

        raise GroupError(ErrorCodes.STUDENT_NOT_IN_GROUP, group_set=group_set_id)

    def get_groups_for_grading(
        self, svc, course, group_set_id, grading_student_id=None
    ):
        return svc.get_course_groupings_for_user(
            course, grading_student_id, type_=self.group_type, group_set_id=group_set_id
        )

    def get_groups_for_instructor(self, _svc, course, group_set_id):
        try:
            groups = self._blackboard_api.group_set_groups(course.lms_id, group_set_id)
        except ExternalRequestError as exc:
            if exc.status_code == 404:
                raise GroupError(
                    ErrorCodes.GROUP_SET_NOT_FOUND, group_set=group_set_id
                ) from exc

            raise

        if not groups:
            raise GroupError(ErrorCodes.GROUP_SET_EMPTY, group_set=group_set_id)

        return groups
